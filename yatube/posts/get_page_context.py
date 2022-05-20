from django.conf import settings
from django.core.paginator import Paginator


def get_page_context(request, posts):
    paginator = Paginator(posts, settings.POST_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
