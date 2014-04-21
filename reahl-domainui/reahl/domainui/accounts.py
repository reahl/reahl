# Copyright 2012, 2013 Reahl Software Services (Pty) Ltd. All rights reserved.
# -*- encoding: utf-8 -*-
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

"""A user interface for logging in, registering, etc using :class:`~reahl.systemaccountmodel.EmailAndPasswordSystemAccount`."""


from reahl.component.i18n import Translator
from reahl.web.fw import UserInterface, Widget, WebExecutionContext, Url
from reahl.web.ui import Form, InputGroup, LabelledBlockInput, Button, CheckboxInput, \
                         TextInput, PasswordInput, H, P, A, Div, CueInput,\
                         CheckCheckboxButton, PopupA, DialogButton, ErrorFeedbackMessage

from reahl.component.modelinterface import RemoteConstraint, Action, exposed
from reahl.component.decorators import deprecated
from reahl.systemaccountmodel import EmailAndPasswordSystemAccount, NotUniqueException, NewPasswordRequest, \
     AccountManagementInterface

_ = Translator(u'reahl-domainui')


class TitledWidget(Widget):
    def __init__(self, view):
        super(TitledWidget, self).__init__(view)
        self.add_child(H(view, 1, text=view.title))


class ActionButtonGroup(InputGroup):
    def __init__(self, view, label_text=None):
        super(ActionButtonGroup, self).__init__(view, label_text=label_text)
        self.add_to_attribute(u'class', [u'action_buttons'])


class LoginForm(Form):
    def __init__(self, view, event_channel_name, account_management_interface):
        super(LoginForm, self).__init__(view, event_channel_name)
        self.account_management_interface = account_management_interface

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))
        
        login_inputs = self.add_child(InputGroup(view, label_text=_(u'Please specify:')))
        email_cue = P(view, _(u'The email address you used to register here.'))
        login_inputs.add_child(CueInput(TextInput(self, self.account_management_interface.fields.email), email_cue))
        
        password_cue = P(view, _(u'The secret password you supplied upon registration.') )
        password_cue_input = CueInput(PasswordInput(self, self.account_management_interface.fields.password), password_cue)
        forgot_password_bookmark = self.user_interface.get_bookmark(relative_path=u'/resetPassword',
                                                            description=_(u'Forgot your password?'))
        password_cue_input.input_part.add_child(A.from_bookmark(view, forgot_password_bookmark))
        login_inputs.add_child(password_cue_input)
        stay_cue = P(view, _(u'If selected, you will stay logged in for longer.'))
        login_inputs.add_child(CueInput(CheckboxInput(self, self.account_management_interface.fields.stay_logged_in), stay_cue))

        login_buttons = self.add_child(ActionButtonGroup(view))
        login_buttons.add_child(Button(self, account_management_interface.events.login_event))


class LoginWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(LoginWidget, self).__init__(view)
        self.add_child(LoginForm(view, u'login_form', account_management_interface))


class UniqueEmailConstraint(RemoteConstraint):
    def validate_parsed_value(self, email):
        try:
            EmailAndPasswordSystemAccount.assert_email_unique(email)
        except NotUniqueException:
            raise self


class RegisterWidget(TitledWidget):
    def __init__(self, view, bookmarks, account_management_interface):
        super(RegisterWidget, self).__init__(view)
        self.add_child(RegisterForm(view, u'register', bookmarks, account_management_interface))


class RegisterForm(Form):
    def __init__(self, view, event_channel_name, bookmarks, account_management_interface):
        super(RegisterForm, self).__init__(view, event_channel_name)
        self.bookmarks = bookmarks
        self.account_management_interface = account_management_interface

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))
        
        self.create_identification_inputs()
        self.create_terms_inputs()
        self.create_action_buttons()
        
    def create_identification_inputs(self):
        identification_inputs = self.add_child(InputGroup(self.view, label_text=_(u'How will you identify yourself?')))
        
        email_cue = P(self.view, _(u'You identify yourself to us by your email address.' \
                                   u'This information is not divulged to others.'))
        error_message=_(u'Sorry, you can only register once per email address and someone is ' \
                        u'already registered as $value. Did you perhaps register long ago?')
                        
        unique_email_field = self.account_management_interface.fields.email.as_with_validation_constraint(UniqueEmailConstraint(error_message))
        identification_inputs.add_child(CueInput(TextInput(self, unique_email_field), email_cue))
        
        password_cue = P(self.view, _(u'Upon logging in, you will be asked for your password. Your password should be a '\
                                 u'secret, known only to yourself, and be difficult to guess.') )
        identification_inputs.add_child(CueInput(PasswordInput(self, self.account_management_interface.fields.password), 
                                           password_cue))
        repeat_password_cue = P(self.view, _(u'By typing the same password again you help us to make sure you did not make any typing mistakes.'))
        identification_inputs.add_child(CueInput(PasswordInput(self, self.account_management_interface.fields.repeat_password), 
                                           repeat_password_cue))

    def create_terms_inputs(self):
        terms_inputs = self.add_child(InputGroup(self.view, label_text=_(u'Terms and conditions')))

        terms_prompt = P(self.view, text=_(u'Please read and accept our {terms}. You may also be interested '
                                           u'to read our {privacypolicy} and our {disclaimer}.'))
        popup = PopupA(self.view, self.bookmarks.terms_bookmark, '#terms', close_button=False)
        terms_inputs.add_child(terms_prompt.format(terms=popup,
                                                   privacypolicy=PopupA(self.view, self.bookmarks.privacy_bookmark, '#privacypolicy'),
                                                   disclaimer=PopupA(self.view, self.bookmarks.disclaimer_bookmark, '#disclaimer')))
        
        terms_cue = P(self.view, _(u'You can only register if you agree to the terms and conditions.'))
        accept_checkbox = CheckboxInput(self, self.account_management_interface.fields.accept_terms)
        terms_inputs.add_child(CueInput(accept_checkbox, terms_cue))

        popup.add_button(CheckCheckboxButton(_(u'Accept'), accept_checkbox))
        popup.add_button(DialogButton(_(u'Cancel')))
    
    def create_action_buttons(self):
        actions = self.add_child(ActionButtonGroup(self.view))
        actions.add_child(Button(self, self.account_management_interface.events.register_event))


class VerifyEmailWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(VerifyEmailWidget, self).__init__(view)
        self.add_child(VerifyForm(view, u'verify', account_management_interface))


class VerifyForm(Form):
    def __init__(self, view, event_channel_name, account_management_interface):
        self.account_management_interface = account_management_interface
        super(VerifyForm, self).__init__(view, event_channel_name)
        
        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        identification_inputs = self.add_child(InputGroup(view, label_text=_(u'Please supply the following details')))
        identification_inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.email)))
        identification_inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.secret)))
        identification_inputs.add_child(LabelledBlockInput(PasswordInput(self, account_management_interface.fields.password)))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.verify_event))

    @exposed
    def query_fields(self, fields):
        fields.email = self.account_management_interface.fields.email.as_optional()
        fields.secret = self.account_management_interface.fields.secret.as_optional()

class RegisterHelpWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(RegisterHelpWidget, self).__init__(view)
        self.add_child(RegisterHelpForm(view, account_management_interface))


class RegisterHelpForm(Form):
    def __init__(self, view, account_management_interface):
        super(RegisterHelpForm, self).__init__(view, u'register_help')

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))
        
        inputs = self.add_child(InputGroup(view, label_text=_(u'Please supply the email address you tried to register with.')))
        inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.email)))
        
        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.investigate_event))


class RegistrationDuplicatedWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(RegistrationDuplicatedWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'You are trying to register using the email address "%s"') % account_management_interface.email))
        self.add_child(P(view, text=_(u'That address is already registered and active on the system.' \
                                      u'This means that you (or someone else) must have registered using that email address' \
                                      u' previously.')))

        forgot_password_bookmark = self.user_interface.get_bookmark(relative_path=u'/resetPassword')
        last_p = P(view, text=_(u'You can gain access to this account by following our {procedure}.'))
        self.add_child(last_p.format(procedure=A.from_bookmark(view, forgot_password_bookmark.with_description(_(u' password reset procedure')))))

        
class RegistrationPendingWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(RegistrationPendingWidget, self).__init__(view)
        config = WebExecutionContext.get_context().config
        self.add_child(P(view, text=_(u'There is a registration pending for email address "%s".') % account_management_interface.email))
        self.add_child(P(view, text=_(u'Before you can log in using it, you need to act on the automated email '\
                                      u'sent to that address. It looks like you did not do that.')))
        self.add_child(P(view, text=_(u'You should receive the automated email anything between a minute to an hour after '\
                                      u'registration. Sometimes though, your email software may mistakenly identify our '\
                                      u'email as junk email. If this happens it will be hidden away in a "junk email" '\
                                      u'folder or just not shown to you.')))
        self.add_child(P(view, text=_(u'You can have the email re-sent to you by clicking on the button below.')))
        self.add_child(P(view, text=_(u'Before you do that, however, please make sure that your email system will allow '\
                                      u'emails from "%s" through to you.') % config.accounts.admin_email))

        self.add_child(RegistrationPendingForm(view))


class RegistrationPendingForm(Form):
    def __init__(self, view):
        super(RegistrationPendingForm, self).__init__(view, u'register_pending')

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))
        
        actions = self.add_child(ActionButtonGroup(view, label_text=_(u'Re-send registration email')))
        actions.add_child(Button(self, self.user_interface.account_management_interface.events.resend_event))


class RegistrationNotFoundWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(RegistrationNotFoundWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'There is no record of someone trying to register the email address "%s".') % account_management_interface.email))
        self.add_child(P(view, text=_(u'Perhaps you mistyped your email address when registering? The system also removes ' \
                                      u'such a registration request if you take a long time to get around to verifying it.')))

        register_bookmark = self.user_interface.get_bookmark(relative_path=u'/register')
        last_p = P(view, text=_(u'Whatever the case, please {register} to rectify the problem.'))
        self.add_child(last_p.format(register=A.from_bookmark(view, register_bookmark.with_description(_(u'register again')))))


class RegistrationEmailSentWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(RegistrationEmailSentWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'A new registration email was sent to "%s"') % account_management_interface.email))
        self.add_child(P(view, text=_(u'Please watch your inbox and follow the instructions in the email.')))

    

class ThanksWidget(TitledWidget):
    def __init__(self, view):
        super(ThanksWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'Thank you for verifying your email address.')))
        self.add_child(P(view, text=_(u'Your account is now active, and you can proceed to log in using the details you provided.')))


class CongratsWidget(TitledWidget):
    def __init__(self, view, account_management_interface, register_help_bookmark):
        super(CongratsWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'You have successfully registered.')))
        self.add_child(P(view, text=_(u'Before we can allow you to log in, however, you need to prove to us that you are indeed the owner of %s.') % account_management_interface.email))
        self.add_child(P(view, text=_(u'You can do that by following instructions just emailed to that address.')))
        self.add_child(P(view, text=_(u'Sometimes these emails arrive immediately, but they may also be delayed.')))
        last_p = P(view, text=_(u'If you do not receive the email within an hour or so, please follow {trouble}.'))
        self.add_child(last_p.format(trouble=A.from_bookmark(view, register_help_bookmark.with_description(_(u'our troubleshooting procedure')))))


class ResetPasswordWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(ResetPasswordWidget, self).__init__(view)
        explanation = P(view, text=_(u'To ensure you are not an impostor, resetting your password is a two step '\
                         u'process: First, we send a "secret key" to your registered email address. '\
                         u'Then, {choose_password}. But you need that secret key for the last step in order to prove '\
                         u'that you are indeed the owner of the registered email address.'))
        link_text = _(u'you can choose a new password')
        step2_bookmark = self.user_interface.get_bookmark(relative_path=u'/choosePassword', description=link_text)
        self.add_child(explanation.format(choose_password=A.from_bookmark(view, step2_bookmark)))
        self.add_child(ResetPasswordForm(view, account_management_interface))


class ResetPasswordForm(Form):
    def __init__(self, view, account_management_interface):
        super(ResetPasswordForm, self).__init__(view, u'reset_password')

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        inputs = self.add_child(InputGroup(view, label_text=_(u'Request a secret key')))
        inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.email)))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.reset_password_event))


class ChoosePasswordWidget(TitledWidget):
    def __init__(self, view, account_management_interface):
        super(ChoosePasswordWidget, self).__init__(view)
        explanation = P(view, text=_(u'Do you have your secret key? You can only choose a new password if you {reset_password}.'))
        
        link_text = _(u'previously requested a secret key to be sent to your registered email address')
        step1_bookmark = self.user_interface.get_bookmark(relative_path=u'/resetPassword', description=link_text)

        self.add_child(explanation.format(reset_password=A.from_bookmark(view, step1_bookmark)))
        self.add_child(ChoosePasswordForm(view, account_management_interface))


class ChoosePasswordForm(Form):
    def __init__(self, view, account_management_interface):
        self.account_management_interface = account_management_interface
        super(ChoosePasswordForm, self).__init__(view, u'choose_password')

        if self.exception:
            self.add_child(ErrorFeedbackMessage(view, self.exception.as_user_message()))

        inputs = self.add_child(InputGroup(view, label_text=_(u'Choose a new password')))
        inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.email)))
        inputs.add_child(LabelledBlockInput(TextInput(self, account_management_interface.fields.secret)))
        inputs.add_child(LabelledBlockInput(PasswordInput(self, account_management_interface.fields.password)))
        inputs.add_child(LabelledBlockInput(PasswordInput(self, account_management_interface.fields.repeat_password)))

        actions = self.add_child(ActionButtonGroup(view))
        actions.add_child(Button(self, account_management_interface.events.choose_password_event))

    @exposed
    def query_fields(self, fields):
        fields.email = self.account_management_interface.fields.email.as_optional()
        fields.secret = self.account_management_interface.fields.secret.as_optional()


class PasswordChangedWidget(TitledWidget):
    def __init__(self, view):
        super(PasswordChangedWidget, self).__init__(view)
        self.add_child(P(view, text=_(u'Thank you, your password has been changed successfully.')))


class AccountUI(UserInterface):
    """A user-facing UserInterface for logging in and managing your own login.

       **Slots:**
         - main_slot: All UI elements are put into this Slot for any View in this UserInterface.
         
       **Views**
         Call :meth:`AccountUI.get_bookmark` passing one of these relative URLs as the `relative_url` kwarg
         in order to get a Bookmark for the View listed below:

         `/register`
           Here new users can register new user accounts on the system.
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
        
          :param bookmarks: An object with the following attributes, each of which is a Bookmark instance to a View\
              explaining the listed legal document:
              
                - terms_bookmark: the terms of service
                - privacy_bookmark: the privacy policy
                - disclaimer_bookmark the disclaimer
        """
        self.bookmarks = bookmarks
        self.account_management_interface = AccountManagementInterface.for_current_session()
        self.assemble_login()
        self.assemble_reset_password()
        self.assemble_register_help()
        self.assemble_register()

    def assemble_login(self):
        login_local = self.define_view(u'/login', title=_(u'Log in with email and password'), detour=True)
        login_local.set_slot(u'main_slot', LoginWidget.factory(self.account_management_interface))

        self.define_return_transition(self.account_management_interface.events.login_event, login_local)


    def assemble_reset_password(self):
        reset_password = self.define_view(u'/resetPassword', title=_(u'Reset a password: Step 1'))
        reset_password.set_slot(u'main_slot', ResetPasswordWidget.factory(self.account_management_interface))
        
        choose_password = self.define_view(u'/choosePassword', title=_(u'Reset a password: Step 2'))
        choose_password.set_slot(u'main_slot', ChoosePasswordWidget.factory(self.account_management_interface))
        
        password_changed = self.define_view(u'/passwordChanged', title=_(u'Password change complete'))
        password_changed.set_slot(u'main_slot', PasswordChangedWidget.factory())

        self.define_transition(self.account_management_interface.events.reset_password_event, 
                            reset_password, choose_password)
        self.define_transition(self.account_management_interface.events.choose_password_event, 
                            choose_password, password_changed )


    def assemble_register_help(self):
        register_help = self.define_view(u'/registerHelp', title=_(u'Problems registering?'))
        register_help.set_slot(u'main_slot', RegisterHelpWidget.factory(self.account_management_interface))
        
        help_duplicate = self.define_view(u'/registerHelp/duplicate', title=_(u'Address already registered'))
        help_duplicate.set_slot(u'main_slot', RegistrationDuplicatedWidget.factory(self.account_management_interface))
        
        help_pending = self.define_view(u'/registerHelp/pending', title=_(u'Registration still pending'))
        help_pending.set_slot(u'main_slot', RegistrationPendingWidget.factory(self.account_management_interface))
        
        help_reregister = self.define_view(u'/registerHelp/reregister', title=_(u'Registration not found'))
        help_reregister.set_slot(u'main_slot', RegistrationNotFoundWidget.factory(self.account_management_interface))
        
        help_sent = self.define_view(u'/registerHelp/pending/sent', title=_(u'Registration email sent'))
        help_sent.set_slot(u'main_slot', RegistrationEmailSentWidget.factory(self.account_management_interface))
        
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
        self.register_help_bookmark = register_help.as_bookmark(self)


    def assemble_register(self):
        register = self.define_view(u'/register', title=_(u'Register with us'))
        register.set_slot(u'main_slot', RegisterWidget.factory(self.bookmarks, self.account_management_interface))
        
        congrats = self.define_view(u'/congrats', title=_(u'Congratulations'))
        congrats.set_slot(u'main_slot', CongratsWidget.factory(self.account_management_interface, self.register_help_bookmark))
        
        verify = self.define_view(u'/verify', title=_(u'Verify pending registration'))
        verify.set_slot(u'main_slot', VerifyEmailWidget.factory(self.account_management_interface))
        
        thanks = self.define_view(u'/thanks', title=_(u'Thanks for all your troubles'))
        thanks.set_slot(u'main_slot', ThanksWidget.factory())

        self.define_transition(self.account_management_interface.events.register_event, register, congrats)
        self.define_transition(self.account_management_interface.events.verify_event, verify, thanks)


@deprecated(u'Please use AccountUI instead.')
class AccountRegion(AccountUI):
    pass


