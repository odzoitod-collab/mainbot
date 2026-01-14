"""Finite State Machine (FSM) states for bot flows."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    """States for user registration flow."""
    waiting_for_agreement = State()
    waiting_for_age = State()
    waiting_for_exp_confirm = State()
    waiting_for_work_hours = State()
    waiting_for_motivation = State()
    waiting_for_source = State()


class AdminProfitState(StatesGroup):
    """States for admin profit management flow."""
    waiting_for_worker_username = State()
    waiting_for_mammoth_name = State()
    waiting_for_service = State()
    waiting_for_amount = State()
    waiting_for_percent = State()
    waiting_for_stage = State()  # deposit/tax
    waiting_for_confirm = State()


class AdminContentState(StatesGroup):
    """States for admin content management flow."""
    waiting_for_category = State()
    waiting_for_action = State()  # add/delete
    waiting_for_resource_type = State()  # community/resource
    waiting_for_data = State()


class AdminMentorState(StatesGroup):
    """States for admin mentor management flow."""
    waiting_for_user_id = State()
    waiting_for_service = State()
    waiting_for_percent = State()


class AdminBroadcastState(StatesGroup):
    """States for admin broadcast flow."""
    waiting_for_title = State()
    waiting_for_text = State()
    waiting_for_button = State()
    waiting_for_confirm = State()


class AdminQuestionState(StatesGroup):
    """States for admin question management flow."""
    waiting_for_question = State()


class SettingsState(StatesGroup):
    """States for user settings flow."""
    waiting_for_wallet = State()


class AdminDirectPaymentState(StatesGroup):
    """States for admin direct payment settings flow."""
    waiting_for_requisites = State()
    waiting_for_additional_info = State()
    waiting_for_support_username = State()


class CommunityCreateState(StatesGroup):
    """States for community creation flow."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_chat_link = State()
    waiting_for_confirm = State()

class MentorBroadcastState(StatesGroup):
    """States for mentor broadcast flow."""
    waiting_for_message = State()
    waiting_for_photo = State()
    waiting_for_confirm = State()


class MentorChannelState(StatesGroup):
    """States for mentor channel management flow."""
    waiting_for_channel_name = State()
    waiting_for_channel_description = State()
    waiting_for_channel_link = State()
    waiting_for_confirm = State()


class ChangeTagState(StatesGroup):
    """States for tag change flow."""
    waiting_for_tag = State()