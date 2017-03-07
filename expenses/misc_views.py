from django.http import Http404, JsonResponse
from expenses.models import Committee

def budget(request):
    if request.method != 'GET':
        raise Http404()
    return JsonResponse({'committees': [committee.get_overview_dict() for committee in Committee.objects.all()]})
