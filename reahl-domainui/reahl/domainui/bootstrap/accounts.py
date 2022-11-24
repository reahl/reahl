# Copyright 2013-2022 Reahl Software Services (Pty) Ltd. All rights reserved.
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

""".. versionadded:: 3.2

A user interface for logging in, registering, etc using
:class:`~reahl.domain.systemaccountmodel.EmailAndPasswordSystemAccount`.

"""


from reahl.component.i18n import Catalogue
from reahl.component.context import ExecutionContext
from reahl.web.fw import UserInterface
from reahl.web.fw import Widget
from reahl.web.bootstrap.ui import H, P, A, Alert
from reahl.web.bootstrap.forms import Button, CueInput, TextInput, PasswordInput, \
    FieldSet, Form, FormLayout, CheckboxInput, TextNode
from reahl.web.bootstrap.popups import PopupA, CheckCheckboxScript

from reahl.component.modelinterface import RemoteConstraint, Action, ExposedNames
from reahl.domain.systemaccountmodel import EmailAndPasswordSystemAccount, NotUniqueException,\
    AccountManagementInterface

_ = Catalogue('reahl-domainui')


class TitledWidget(Widget):
    def __init__(self, view):
        super().__init__(view)
        self.add_child(H(view, 1, text=view.title))


class ActionButtonGroup(FieldSet):
    def __init__(self, view, legend_text=None):
        super().__init__(view, legend_text=legend_text)
        self.add_to_attribute('class', ['action_buttons'])


class LoginForm(Form):
    def __init__(self, view, event_channel_name, account_management_interface):
        super().__init__(view, event_channel_name)
        self.account_management_interface = account_management_interface

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        login_inputs = self.add_child(FieldSet(view, legend_text=_('Please specify'))).use_layout(FormLayout())
        email_cue = P(view, _('The email address you used to register here.'))
        login_inputs.layout.add_input(CueInput(TextInput(self, self.account_management_interface.fields.email), email_cue))

        password_cue = P(view, _('The secret password you supplied upon registration.') )
        password_cue_input = CueInput(PasswordInput(self, self.account_management_interface.fields.password), password_cue)
        forgot_password_bookmark = self.user_interface.get_bookmark(relative_path='/resetPassword',
                                                            description=_('Forgot your password?'))
        
        password_cue_input.add_child(A.from_bookmark(view, forgot_password_bookmark))
        login_inputs.layout.add_input(password_cue_input)
        stay_cue = P(view, _('If selected, you will stay logged in for longer.'))
        login_inputs.layout.add_input(CueInput(CheckboxInput(self, self.account_management_interface.fields.stay_logged_in), stay_cue))

        login_buttons = self.add_child(ActionButtonGroup(view))
        btn = login_buttons.add_child(Button(self, account_management_interface.events.login_event, style='primary'))


class LoginWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(LoginForm(view, 'login_form', account_management_interface))


class UniqueEmailConstraint(RemoteConstraint):
    def validate_parsed_value(self, email):
        try:
            EmailAndPasswordSystemAccount.assert_email_unique(email)
        except NotUniqueException:
            raise self


class RegisterWidget(TitledWidget):
    def __init__(self, view, bookmarks, account_management_interface):
        super().__init__(view)
        self.add_child(RegisterForm(view, 'register', bookmarks, account_management_interface))


class RegisterForm(Form):
    def __init__(self, view, event_channel_name, bookmarks, account_management_interface):
        super().__init__(view, event_channel_name)
        self.bookmarks = bookmarks
        self.account_management_interface = account_management_interface

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        self.create_identification_inputs()
        self.create_terms_inputs()
        self.create_action_buttons()

    def create_identification_inputs(self):
        identification_inputs = self.add_child(FieldSet(self.view, legend_text=_('How will you identify yourself?'))).use_layout(FormLayout())

        email_cue = P(self.view, _('You identify yourself to us by your email address.'
                                   'This information is not divulged to others.'))
        error_message = _('Sorry, you can only register once per email address and someone is '
                          'already registered as $value. Did you perhaps register long ago?')

        unique_email_field = self.account_management_interface.fields.email.with_validation_constraint(UniqueEmailConstraint(error_message))
        identification_inputs.layout.add_input(CueInput(TextInput(self, unique_email_field), email_cue))

        password_cue = P(self.view, _('Upon logging in, you will be asked for your password. Your password should be a '
                                      'secret, known only to yourself, and be difficult to guess.') )
        identification_inputs.layout.add_input(CueInput(PasswordInput(self, self.account_management_interface.fields.password),
                                           password_cue))
        repeat_password_cue = P(self.view, _('By typing the same password again you help us to make sure you did not make any typing mistakes.'))
        identification_inputs.layout.add_input(
            CueInput(
                PasswordInput(self, self.account_management_interface.fields.repeat_password), repeat_password_cue))

    def create_terms_inputs(self):
        terms_inputs = self.add_child(FieldSet(self.view, legend_text=_('Terms and conditions'))).use_layout(FormLayout())

        terms_prompt = P(self.view, text=_('Please read and accept our {terms}. You may also be interested '
                                           'to read our {privacypolicy} and our {disclaimer}.'))
        popup = PopupA(self.view, self.bookmarks.terms_bookmark, '#terms', close_button=False)
        terms_inputs.add_child(terms_prompt.format(terms=popup,
                                                   privacypolicy=PopupA(self.view, self.bookmarks.privacy_bookmark, '#privacypolicy'),
                                                   disclaimer=PopupA(self.view, self.bookmarks.disclaimer_bookmark, '#disclaimer')))

        terms_cue = P(self.view, _('You can only register if you agree to the terms and conditions.'))
        accept_checkbox = CheckboxInput(self, self.account_management_interface.fields.accept_terms)
        terms_inputs.layout.add_input(CueInput(accept_checkbox, terms_cue))

        popup.add_js_button(_('Accept'), CheckCheckboxScript(accept_checkbox), style='primary')
        popup.add_js_button(_('Cancel'))

    def create_action_buttons(self):
        actions = self.add_child(ActionButtonGroup(self.view))
        actions.add_child(Button(self, self.account_management_interface.events.register_event, style='primary'))


class VerifyEmailWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(VerifyForm(view, 'verify', account_management_interface))


class VerifyForm(Form):
    def __init__(self, view, event_channel_name, account_management_interface):
        self.account_management_interface = account_management_interface
        super().__init__(view, event_channel_name)

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        identification_inputs = self.add_child(FieldSet(view, legend_text=_('Please supply the following details'))).use_layout(FormLayout())

        identification_inputs.layout.add_input(TextInput(self, account_management_interface.fields.email))
        identification_inputs.layout.add_input(TextInput(self, account_management_interface.fields.secret))
        identification_inputs.layout.add_input(PasswordInput(self, account_management_interface.fields.password))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.verify_event, style='primary'))

    query_fields = ExposedNames()
    query_fields.email = lambda i: i.account_management_interface.fields.email.as_optional()
    query_fields.secret = lambda i: i.account_management_interface.fields.secret.as_optional()


class RegisterHelpWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(RegisterHelpForm(view, account_management_interface))


class RegisterHelpForm(Form):
    def __init__(self, view, account_management_interface):
        super().__init__(view, 'register_help')

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))
        
        inputs = self.add_child(FieldSet(view, legend_text=_('Please supply the email address you tried to register with.'))).use_layout(FormLayout())
        inputs.layout.add_input(TextInput(self, account_management_interface.fields.email),
                                help_text=_('Please supply the email address you tried to register with.'))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.investigate_event, style='primary'))


class RegistrationDuplicatedWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(P(view, text=_('You are trying to register using the email address "%s"') % account_management_interface.email))
        self.add_child(P(view, text=_('That address is already registered and active on the system.'
                                      'This means that you (or someone else) must have registered using that email address'
                                      ' previously.')))

        forgot_password_bookmark = self.user_interface.get_bookmark(relative_path='/resetPassword')
        last_p = P(view, text=_('You can gain access to this account by following our {procedure}.'))
        self.add_child(last_p.format(procedure=A.from_bookmark(view, forgot_password_bookmark.with_description(_(' password reset procedure')))))

        
class RegistrationPendingWidget(TitledWidget):
    def __init__(self, view, account_management_interface, verify_bookmark):
        super().__init__(view)
        config = ExecutionContext.get_context().config
        self.add_child(P(view, text=_('There is a registration pending for email address "%s".') % account_management_interface.email))
        self.add_child(P(view, text=_('Before you can log in, you need to verify your email address using the secret key '
                                      'sent to that address. It looks like you did not do that.')))
        self.add_child(P(view, text=_('You should receive the automated email anything between a minute to an hour after '
                                      'registration. Sometimes though, your email software may mistakenly identify our '
                                      'email as junk email. If this happens it will be hidden away in a "junk email" '
                                      'folder or just not shown to you.')))        
        self.add_child(P(view, text=_('You can have the email re-sent to you by clicking on the button below.')))
        self.add_child(P(view, text=_('Before you do that, however, please make sure that your email system will allow '
                                      'emails from "%s" through to you.') % config.accounts.admin_email))
        self.add_child(P(view, text=_('Sometimes these emails arrive immediately, but they may also be delayed.')))
        p = P(view, text=_('Once you located the email, retrieve the code and then enter it on {verify}.'))
        self.add_child(p.format(verify=A.from_bookmark(view, verify_bookmark.with_description(_('the verification page')))))


        self.add_child(RegistrationPendingForm(view))


class RegistrationPendingForm(Form):
    def __init__(self, view):
        super().__init__(view, 'register_pending')

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))
        
        actions = self.add_child(ActionButtonGroup(view, legend_text=_('Re-send registration email')))
        actions.add_child(Button(self, self.user_interface.account_management_interface.events.resend_event, style='primary'))


class RegistrationNotFoundWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(P(view, text=_('There is no record of someone trying to register the email address "%s".') % account_management_interface.email))
        self.add_child(P(view, text=_('Perhaps you mistyped your email address when registering? The system also removes '
                                      'such a registration request if you take a long time to get around to verifying it.')))

        register_bookmark = self.user_interface.get_bookmark(relative_path='/register')
        last_p = P(view, text=_('Whatever the case, please {register} to rectify the problem.'))
        self.add_child(last_p.format(register=A.from_bookmark(view, register_bookmark.with_description(_('register again')))))


class RegistrationEmailSentWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        self.add_child(P(view, text=_('A new registration email was sent to "%s"') % account_management_interface.email))
        self.add_child(P(view, text=_('Please watch your inbox and follow the instructions in the email.')))

    

class ThanksWidget(TitledWidget):
    def __init__(self, view):
        super().__init__(view)
        self.add_child(P(view, text=_('Thank you for verifying your email address.')))
        self.add_child(P(view, text=_('Your account is now active, and you can proceed to log in using the details you provided.')))


class CongratsWidget(TitledWidget):
    def __init__(self, view, account_management_interface, register_help_bookmark, verify_bookmark):
        super().__init__(view)
        self.add_child(P(view, text=_('You have successfully registered.')))
        self.add_child(P(view, text=_('Before we can allow you to log in, however, you need to prove to us that you are indeed the owner of %s.') % account_management_interface.email))
        p = P(view, text=_('In order to do this, an email was sent to {email} containing a secret code. '
                           'Please check your email, retrieve the code and then enter it on {verify}.'))
        self.add_child(p.format(verify=A.from_bookmark(view, verify_bookmark.with_description(_('the verification page'))),
                                email=TextNode(view, account_management_interface.email)))
        self.add_child(P(view, text=_('Sometimes these emails arrive immediately, but they may also be delayed.')))
        last_p = P(view, text=_('If you do not receive the email within an hour or so, please follow {trouble}.'))
        self.add_child(last_p.format(trouble=A.from_bookmark(view, register_help_bookmark.with_description(_('our troubleshooting procedure')))))


class ResetPasswordWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        explanation = P(view,
                        text=_('To ensure you are not an impostor, resetting your password is a two step '
                               'process: First, we send a "secret key" to your registered email address. '
                               'Then, {choose_password}. But you need that secret key for the last step in order to prove '
                               'that you are indeed the owner of the registered email address.'))
        link_text = _('you can choose a new password')
        step2_bookmark = self.user_interface.get_bookmark(relative_path='/choosePassword', description=link_text)
        self.add_child(explanation.format(choose_password=A.from_bookmark(view, step2_bookmark)))
        self.add_child(ResetPasswordForm(view, account_management_interface))


class ResetPasswordForm(Form):
    def __init__(self, view, account_management_interface):
        super().__init__(view, 'reset_password')

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        inputs = self.add_child(FieldSet(view, legend_text=_('Request a secret key'))).use_layout(FormLayout())
        inputs.layout.add_input(TextInput(self, account_management_interface.fields.email))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.reset_password_event, style='primary'))


class ChoosePasswordWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super().__init__(view)
        explanation = P(view, text=_('Do you have your secret key? You can only choose a new password if you {reset_password}.'))
        
        link_text = _('previously requested a secret key to be sent to your registered email address')
        step1_bookmark = self.user_interface.get_bookmark(relative_path='/resetPassword', description=link_text)

        self.add_child(explanation.format(reset_password=A.from_bookmark(view, step1_bookmark)))
        self.add_child(ChoosePasswordForm(view, account_management_interface))


class ChoosePasswordForm(Form):
    def __init__(self, view, account_management_interface):
        self.account_management_interface = account_management_interface
        super().__init__(view, 'choose_password')

        if self.exception:
            self.add_child(Alert(view, self.exception.as_user_message(), 'warning'))

        inputs = self.add_child(FieldSet(view, legend_text=_('Choose a new password'))).use_layout(FormLayout())
        inputs.layout.add_input(TextInput(self, account_management_interface.fields.email))
        inputs.layout.add_input(TextInput(self, account_management_interface.fields.secret))
        inputs.layout.add_input(PasswordInput(self, account_management_interface.fields.password))
        inputs.layout.add_input(PasswordInput(self, account_management_interface.fields.repeat_password))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.choose_password_event, style='primary'))

    query_fields = ExposedNames()
    query_fields.email = lambda i: i.account_management_interface.fields.email.as_optional()
    query_fields.secret = lambda i: i.account_management_interface.fields.secret.as_optional()


class PasswordChangedWidget(TitledWidget):
    def __init__(self, view):
        super().__init__(view)
        self.add_child(P(view, text=_('Thank you, your password has been changed successfully.')))


class AccountUI(UserInterface):
    """A user-facing UserInterface for logging in and managing your own login.

       **Slots:**
         - main_slot: All UI elements are put into this Slot for any View in this UserInterface.
         
       **Views**
         Call :meth:`AccountUI.get_bookmark` passing one of these relative URLs as the `relative_url` kwarg
         in order to get a Bookmark for the View listed below:

         `/register`
           Here new users can register new user accounts on the system.
         `/verify`
           This is where users enter their initial registration verification code that was sent to them via email.
         `/registerHelp`
           Here users can enquire what the status is of their registration. A registration\
                           may be pending because the user has not responded on a verification email, for example.
         `/login`
           Here users can log in using an existing account.
         `/resetPassword`
           This is the first step of resetting a user's password.\
                            Resetting a password is a two-step process: the user first requests it, and then\
                            chooses a new password. In the first step, a secret is emailed to the registered email\
                            address. This has to be supplied during the second step.
         `/choosePassword`
           This is the second (password choosing) step of resetting a user password.
    """
    def assemble(self, bookmarks=None):
        """Assemble this AccountUI.
        
          :keyword bookmarks: An object with the following attributes, each of which is a Bookmark instance to a View\
              explaining the listed legal document:
              
                - terms_bookmark: the terms of service
                - privacy_bookmark: the privacy policy
                - disclaimer_bookmark the disclaimer
        """
        self.bookmarks = bookmarks
        self.account_management_interface = AccountManagementInterface.for_current_session()
        self.assemble_login()
        self.assemble_reset_password()
        self.assemble_register()

    def assemble_login(self):
        login_local = self.define_view('/login', title=_('Log in with email and password'), detour=True)
        login_local.set_slot('main_slot', LoginWidget.factory(self.account_management_interface))

        self.define_return_transition(self.account_management_interface.events.login_event, login_local)

    def assemble_reset_password(self):
        reset_password = self.define_view('/resetPassword', title=_('Reset a password: Step 1'))
        reset_password.set_slot('main_slot', ResetPasswordWidget.factory(self.account_management_interface))
        
        choose_password = self.define_view('/choosePassword', title=_('Reset a password: Step 2'))
        choose_password.set_slot('main_slot', ChoosePasswordWidget.factory(self.account_management_interface))
        
        password_changed = self.define_view('/passwordChanged', title=_('Password change complete'))
        password_changed.set_slot('main_slot', PasswordChangedWidget.factory())

        self.define_transition(self.account_management_interface.events.reset_password_event, 
                               reset_password, choose_password)
        self.define_transition(self.account_management_interface.events.choose_password_event, 
                               choose_password, password_changed )

    def assemble_register_help(self, verify_bookmark):
        register_help = self.define_view('/registerHelp', title=_('Problems registering?'))
        register_help.set_slot('main_slot', RegisterHelpWidget.factory(self.account_management_interface))
        
        help_duplicate = self.define_view('/registerHelp/duplicate', title=_('Address already registered'))
        help_duplicate.set_slot('main_slot', RegistrationDuplicatedWidget.factory(self.account_management_interface))
        
        help_pending = self.define_view('/registerHelp/pending', title=_('Registration still pending'))
        help_pending.set_slot('main_slot', RegistrationPendingWidget.factory(self.account_management_interface, verify_bookmark))
        
        help_reregister = self.define_view('/registerHelp/reregister', title=_('Registration not found'))
        help_reregister.set_slot('main_slot', RegistrationNotFoundWidget.factory(self.account_management_interface))
        
        help_sent = self.define_view('/registerHelp/pending/sent', title=_('Registration email sent'))
        help_sent.set_slot('main_slot', RegistrationEmailSentWidget.factory(self.account_management_interface))
        
        investigate_event = self.account_management_interface.events.investigate_event
        self.define_transition(investigate_event, 
                            register_help, help_duplicate,
                            guard=Action(self.account_management_interface.is_login_active))
        self.define_transition(investigate_event, 
                            register_help, help_pending,
                            guard=Action(self.account_management_interface.is_login_pending))
        self.define_transition(self.account_management_interface.events.resend_event, 
                            help_pending, help_sent)
        self.define_transition(investigate_event, 
                            register_help, help_reregister,
                            guard=Action(self.account_management_interface.is_login_available))

        return register_help.as_bookmark(self)

    def assemble_register(self):
        verify = self.define_view('/verify', title=_('Verify pending registration'))
        verify.set_slot('main_slot', VerifyEmailWidget.factory(self.account_management_interface))

        verify_bookmark = verify.as_bookmark(self)
        register_help_bookmark = self.assemble_register_help(verify_bookmark)

        register = self.define_view('/register', title=_('Register with us'))
        register.set_slot('main_slot', RegisterWidget.factory(self.bookmarks, self.account_management_interface))        

        congrats = self.define_view('/congrats', title=_('Congratulations'))
        congrats.set_slot('main_slot', CongratsWidget.factory(self.account_management_interface, register_help_bookmark, verify_bookmark))
                
        thanks = self.define_view('/thanks', title=_('Thanks for all your troubles'))
        thanks.set_slot('main_slot', ThanksWidget.factory())

        self.define_transition(self.account_management_interface.events.register_event, register, congrats)
        self.define_transition(self.account_management_interface.events.verify_event, verify, thanks)

        return verify_bookmark
