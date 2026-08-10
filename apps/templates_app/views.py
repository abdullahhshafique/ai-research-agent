from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import ResearchTemplate


@login_required
def templates_list(request):
    user_templates = ResearchTemplate.objects.filter(user=request.user)
    public_templates = ResearchTemplate.objects.filter(is_public=True).exclude(user=request.user)

    return render(request, 'pages/templates/list.html', {
        'user_templates': user_templates,
        'public_templates': public_templates
    })


@login_required
def template_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        query_pattern = request.POST.get('query_pattern', '').strip()
        description = request.POST.get('description', '').strip()
        is_public = request.POST.get('is_public') == 'on'

        if not name or not query_pattern:
            messages.error(request, 'Name and query pattern are required.')
            return redirect('templates:templates_list')

        ResearchTemplate.objects.create(
            user=request.user,
            name=name,
            query_pattern=query_pattern,
            description=description,
            is_public=is_public
        )

        messages.success(request, 'Template created!')
        return redirect('templates:templates_list')

    return redirect('templates:templates_list')


@login_required
def template_delete(request, pk):
    template = get_object_or_404(ResearchTemplate, pk=pk, user=request.user)
    template.delete()
    messages.success(request, 'Template deleted.')
    return redirect('templates:templates_list')


@login_required
def template_use(request, pk):
    template = get_object_or_404(ResearchTemplate, pk=pk)

    if not template.is_public and template.user != request.user:
        messages.error(request, 'You do not have permission to use this template.')
        return redirect('templates:templates_list')

    template.increment_usage()

    return redirect(f'/research/?template={pk}')


@login_required
def template_preview(request, template_id):
    """AJAX endpoint to preview template with sample variables."""
    template = get_object_or_404(ResearchTemplate, id=template_id)

    # Check permissions
    if not template.is_public and template.user != request.user:
        raise PermissionDenied

    # Extract variables from pattern
    import re
    variables = re.findall(r'\{(\w+)\}', template.query_pattern)

    # Generate sample fill
    sample_values = {
        'topic': 'artificial intelligence',
        'year': '2026',
        'industry': 'healthcare',
        'technology': 'quantum computing',
        'company': 'OpenAI',
        'region': 'North America',
    }

    sample_query = template.query_pattern
    for var in variables:
        sample_query = sample_query.replace(f'{{{var}}}', sample_values.get(var, f'[{var}]'))

    return JsonResponse({
        "template": {
            "name": template.name,
            "pattern": template.query_pattern,
            "variables": variables,
            "sample_query": sample_query,
            "description": template.description,
        }
    })


@login_required
def template_detail(request, pk):
    template = get_object_or_404(ResearchTemplate, pk=pk)

    if not template.is_public and template.user != request.user:
        raise Http404("Template not found")

    return JsonResponse({
        'name': template.name,
        'query_pattern': template.query_pattern,
        'description': template.description,
        'variables': template.variables
    })