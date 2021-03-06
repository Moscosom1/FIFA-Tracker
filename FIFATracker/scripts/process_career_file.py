import os
import logging

from django.conf import settings
from django.contrib.auth.models import User
from core.models import CareerSaveFileModel
from django.utils.translation import ugettext_lazy as _

from scripts.process_file_utils import parse_career_save
from scripts.delete_user_data import delete_data


def update_savefile_model(cs_model, error, fpath=None):
    if cs_model:
        cs_model.file_process_status_code = 1   # Error Code
        cs_model.file_process_status_msg = error
        cs_model.save()

    try:
        if os.path.exists(fpath):
            os.remove(fpath)
    except PermissionError as e:
        logging.warning("update_savefile_model PermissionError: {}".format(e))
    except TypeError:
        pass


def run(*args):
    user_id = args[0]
    fifa_edition = args[1]

    user = User.objects.get(id=user_id)
    if not user:
        logging.warning(
            "process_career_file script - User not found, ID:{}".format(user_id)
        )
        return

    save_file_model = CareerSaveFileModel.objects.filter(
        user_id=user.id
    ).first()
    if not save_file_model:
        return

    fpath = os.path.join(settings.MEDIA_ROOT, str(save_file_model.uploadedfile))

    if not os.path.exists(fpath):
        update_savefile_model(save_file_model, _("Save file not found on the server."))
        return

    careersave_data_path = os.path.join(settings.MEDIA_ROOT, user.username, "data")

    # Parse Career Save
    try:
        parse_career_save(
            career_file_fullpath=fpath,
            data_path=careersave_data_path,
            user=user,
            slot='1',
            xml_file='',
            fifa_edition=fifa_edition
        )
        user.profile.is_save_processed = True
        user.profile.fifa_edition = fifa_edition
        user.save()
    except FileNotFoundError as e:
        user.profile.is_save_processed = False
        user.save()
        logging.exception(
            "process_career_file script - ParseCareerSave - user: {}".format(user))
    except Exception as e:
        user.profile.is_save_processed = False
        user.save()
        logging.exception(
            "process_career_file script - ParseCareerSave - user: {}".format(user))
        # delete_data(user_id)
        update_savefile_model(save_file_model, e, fpath=fpath)
