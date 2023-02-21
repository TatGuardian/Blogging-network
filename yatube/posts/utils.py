from django.core.paginator import Paginator


def page(request, posts, per_page: int):
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
