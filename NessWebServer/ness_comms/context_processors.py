from .version_info import get_version_info


def version_info(request):
    return {"ness_version_info": get_version_info()}
