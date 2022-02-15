# Copyright 2021 Reahl Software Services (Pty) Ltd. All rights reserved.
#
#    This file is part of Reahl.
#
#    Reahl is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation; version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
CSRF mitigation
"""


import base64
import datetime
import hashlib
import hmac
import logging
import os

from webob.exc import HTTPForbidden

from reahl.component.context import ExecutionContext
from reahl.component.exceptions import DomainException
from reahl.component.modelinterface import ValidationConstraint, InputParseException, Field
from reahl.component.i18n import Catalogue


_ = Catalogue('reahl-web')


class InvalidCSRFToken(Exception):
    pass


class ExpiredCSRFToken(DomainException):
    def __init__(self):
        super().__init__(message=_('This page has expired. For security reasons, please review your input and retry.'),
                         handled_inline=False)

    def __reduce__(self):
        return (self.__class__, ())



class ValidCSRFToken(ValidationConstraint):
    def __init__(self, token):
        super().__init__(error_message=_('Invalid CSRF token.'))
        self.token = token

    def validate_parsed_value(self, parsed_value):
        if not self.token.matches(parsed_value):
            raise HTTPForbidden()
        if parsed_value.is_expired():
            raise ExpiredCSRFToken()

    def validate_input(self, unparsed_input):
        try:
            self.field.parse_input(unparsed_input)
        except InputParseException:
            raise HTTPForbidden()


class CSRFTokenField(Field):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.add_validation_constraint(ValidCSRFToken(token))

    def parse_input(self, unparsed_input):
        try:
            return CSRFToken.from_coded_string(unparsed_input)
        except InvalidCSRFToken as ex:
            logging.getLogger(__name__).warning(str(ex))
            raise InputParseException(ex)

    def unparse_input(self, parsed_value):
        return parsed_value.as_signed_string()


class CSRFToken:
    @classmethod
    def from_coded_string(cls, signed_string):
        try:
            encoded_value, encoded_timestamp, received_signature = signed_string.split(':')
        except (TypeError, ValueError) as e:
            raise InvalidCSRFToken('Malformed incoming token string')

        received_value_string = cls.decode_to_string(encoded_value)
        received_timestamp_string = cls.decode_to_string(encoded_timestamp)

        computed_signature = cls.sign_timed_value(received_value_string, received_timestamp_string)
        is_signature_valid = hmac.compare_digest(received_signature.encode('utf-8'), computed_signature.encode('utf-8'))
        if not is_signature_valid:
            raise InvalidCSRFToken('Invalid signature')

        try:
            timestamp = float(received_timestamp_string)
        except ValueError as e:
            raise InvalidCSRFToken('Unable to parse timestamp')
        if timestamp > cls.get_now().timestamp():
            raise InvalidCSRFToken('Future timestamp')

        return cls(value=received_value_string, timestamp=timestamp)

    @classmethod
    def decode_to_string(cls, encoded_value):
        return base64.urlsafe_b64decode(encoded_value).decode('utf-8')

    @classmethod
    def encode_string(cls, value_string):
        return cls.encode_bytes(value_string.encode('utf-8'))

    @classmethod
    def encode_bytes(cls, bytes):
        return base64.urlsafe_b64encode(bytes).decode('utf-8')

    @classmethod
    def get_now(cls):
        return datetime.datetime.now(tz=datetime.timezone.utc)

    @classmethod
    def get_delimited_encoded_string(cls, value_string, timestamp_string):
        return '%s:%s' % (cls.encode_string(value_string), cls.encode_string(timestamp_string))

    @classmethod
    def sign_timed_value(cls, value_string, timestamp_string):
        timed_value = cls.get_delimited_encoded_string(value_string, timestamp_string)
        key = ExecutionContext.get_context().config.web.csrf_key
        return hmac.new(key.encode('utf-8'), msg=timed_value.encode('utf-8'), digestmod=hashlib.sha1).hexdigest()

    def __init__(self, value=None, timestamp=None):
        self.value = value or hashlib.sha1(os.urandom(64)).hexdigest()
        self.timestamp = timestamp if timestamp else self.get_now().timestamp()

    def as_signed_string(self):
        timestamp_string = repr(self.timestamp)
        signature = self.sign_timed_value(self.value, timestamp_string)
        return '%s:%s' % (self.get_delimited_encoded_string(self.value, timestamp_string), signature)

    def is_expired(self):
        now = self.get_now()
        csrf_timeout_seconds = ExecutionContext.get_context().config.web.csrf_timeout_seconds
        cutoff_timestamp = (now - datetime.timedelta(seconds=csrf_timeout_seconds)).timestamp()
        return self.timestamp < cutoff_timestamp

    def matches(self, other):
        return hmac.compare_digest(self.value, other.value)