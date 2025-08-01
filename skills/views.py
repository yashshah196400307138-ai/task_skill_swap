from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import Skill, SkillCategory, OfferedSkill, DesiredSkill, SkillMatch
from .forms import OfferedSkillForm, DesiredSkillForm, SkillSearchForm

# Create your views here.

class SkillListView(ListView):
    model = Skill
    template_name = 'skills/skill_list.html'
    context_object_name = 'skills'
    
    def get_queryset(self):
        return Skill.objects.filter(category__is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get trending skills based on most offered skills (limited to 15)
        from django.db.models import Count
        trending_skills = (Skill.objects
                          .filter(category__is_active=True)
                          .annotate(offered_count=Count('offered_by_users'))
                          .filter(offered_count__gt=0)
                          .order_by('-offered_count', 'name')[:15])
        
        context['trending_skills'] = trending_skills
        context['categories'] = SkillCategory.objects.filter(is_active=True)
        context['show_more_url'] = 'skills:trending_skills_more'
        
        return context


class SkillCategoryListView(ListView):
    model = SkillCategory   
    template_name = 'skills/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return SkillCategory.objects.filter(is_active=True)


class SkillCategoryDetailView(DetailView):
    model = SkillCategory
    template_name = 'skills/category_detail.html'
    context_object_name = 'category'


class OfferedSkillListView(LoginRequiredMixin, ListView):
    model = OfferedSkill
    template_name = 'skills/offered_list.html'
    context_object_name = 'offered_skills'
    
    def get_queryset(self):
        return OfferedSkill.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['desired_skills'] = self.request.user.desired_skills.all()
        return context


class OfferedSkillCreateView(LoginRequiredMixin, CreateView):
    model = OfferedSkill
    form_class = OfferedSkillForm
    template_name = 'skills/offered_form.html'
    success_url = reverse_lazy('skills:offered_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OfferedSkillUpdateView(LoginRequiredMixin, UpdateView):
    model = OfferedSkill
    form_class = OfferedSkillForm
    template_name = 'skills/offered_form.html'
    success_url = reverse_lazy('skills:offered_list')
    
    def get_queryset(self):
        return OfferedSkill.objects.filter(user=self.request.user)


class OfferedSkillDeleteView(LoginRequiredMixin, DeleteView):
    model = OfferedSkill
    template_name = 'skills/offered_confirm_delete.html'
    success_url = reverse_lazy('skills:offered_list')
    
    def get_queryset(self):
        return OfferedSkill.objects.filter(user=self.request.user)


@login_required
def toggle_offered_skill(request, pk):
    offered_skill = get_object_or_404(OfferedSkill, pk=pk, user=request.user)
    offered_skill.is_active = not offered_skill.is_active
    offered_skill.save()
    return redirect('skills:offered_list')


class DesiredSkillListView(LoginRequiredMixin, ListView):
    model = DesiredSkill
    template_name = 'skills/desired_list.html'
    context_object_name = 'desired_skills'
    
    def get_queryset(self):
        return DesiredSkill.objects.filter(user=self.request.user)


class DesiredSkillCreateView(LoginRequiredMixin, CreateView):
    model = DesiredSkill
    form_class = DesiredSkillForm
    template_name = 'skills/desired_form.html'
    success_url = reverse_lazy('skills:desired_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class DesiredSkillUpdateView(LoginRequiredMixin, UpdateView):
    model = DesiredSkill
    form_class = DesiredSkillForm
    template_name = 'skills/desired_form.html'
    success_url = reverse_lazy('skills:desired_list')
    
    def get_queryset(self):
        return DesiredSkill.objects.filter(user=self.request.user)


class DesiredSkillDeleteView(LoginRequiredMixin, DeleteView):
    model = DesiredSkill
    template_name = 'skills/desired_confirm_delete.html'
    success_url = reverse_lazy('skills:desired_list')
    
    def get_queryset(self):
        return DesiredSkill.objects.filter(user=self.request.user)


@login_required
def toggle_desired_skill(request, pk):
    desired_skill = get_object_or_404(DesiredSkill, pk=pk, user=request.user)
    desired_skill.is_active = not desired_skill.is_active
    desired_skill.save()
    return redirect('skills:desired_list')


class SkillMatchListView(LoginRequiredMixin, ListView):
    model = SkillMatch
    template_name = 'skills/match_list.html'
    context_object_name = 'matches'
    
    def get_queryset(self):
        from django.db.models import Q
        return SkillMatch.objects.filter(
            Q(teacher=self.request.user) | Q(learner=self.request.user),
            is_dismissed=False
        )


@login_required
def dismiss_skill_match(request, pk):
    match = get_object_or_404(SkillMatch, pk=pk)
    match.is_dismissed = True
    match.save()
    return redirect('skills:match_list')


class SkillAutocompleteView(LoginRequiredMixin, ListView):
    model = Skill
    
    def get_queryset(self):
        term = self.request.GET.get('term', '')
        return Skill.objects.filter(name__icontains=term)[:10]
    
    def get(self, request, *args, **kwargs):
        skills = self.get_queryset()
        data = [{'id': skill.id, 'text': skill.name} for skill in skills]
        return JsonResponse({'results': data})


class AddSkillView(LoginRequiredMixin, CreateView):
    model = OfferedSkill
    form_class = OfferedSkillForm
    template_name = 'skills/add_skill.html'
    success_url = '/skills/offered/'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@login_required
def get_skills_by_category(request):
    """AJAX view to get skills by category"""
    category_id = request.GET.get('category_id')
    if category_id:
        skills = Skill.objects.filter(category_id=category_id).order_by('name')
        data = [{'id': skill.id, 'name': skill.name} for skill in skills]
        return JsonResponse({'skills': data})
    return JsonResponse({'skills': []})


class TrendingSkillsMoreView(LoginRequiredMixin, ListView):
    """View to show more trending skills - requires login"""
    model = Skill
    template_name = 'skills/trending_skills_more.html'
    context_object_name = 'trending_skills'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Count
        return (Skill.objects
                .filter(category__is_active=True)
                .annotate(offered_count=Count('offered_by_users'))
                .filter(offered_count__gt=0)
                .order_by('-offered_count', 'name'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Trending Skills'
        return context
