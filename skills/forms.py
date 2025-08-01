from django import forms
from .models import Skill, SkillCategory, OfferedSkill, DesiredSkill

class OfferedSkillForm(forms.ModelForm):
    """Form for creating/editing offered skills"""
    new_skill = forms.CharField(
        max_length=100, required=False,
        label="New Skill (if not listed)",
        help_text="If your skill is not listed above, enter it here."
    )
    skill = forms.ModelChoiceField(
        queryset=None, required=False,
        label="Skill",
        help_text="Select a skill from the list or enter a new one below."
    )
    
    class Meta:
        model = OfferedSkill
        fields = ['skill', 'new_skill', 'proficiency_level', 'description', 'years_of_experience', 'teaching_preference']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Skill
        self.fields['skill'].queryset = Skill.objects.all()
        self.fields['skill'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get('skill')
        new_skill = cleaned_data.get('new_skill')
        user = getattr(self.instance, 'user', None)
        
        if not skill and not new_skill:
            raise forms.ValidationError('Please select a skill or enter a new skill.')
        
        if new_skill:
            from .models import Skill, SkillCategory
            # Assign to a default category if needed
            default_category, _ = SkillCategory.objects.get_or_create(name='Other', defaults={'is_active': True})
            skill_obj, created = Skill.objects.get_or_create(
                name=new_skill.strip(),
                defaults={'category': default_category}
            )
            cleaned_data['skill'] = skill_obj
        
        if cleaned_data.get('skill') and user:
            existing = OfferedSkill.objects.filter(user=user, skill=cleaned_data['skill']).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing.exists():
                raise forms.ValidationError(f'You already offer {cleaned_data["skill"].name}.')
        
        return cleaned_data


class DesiredSkillForm(forms.ModelForm):
    """Form for creating/editing desired skills"""
    
    class Meta:
        model = DesiredSkill
        fields = ['skill', 'urgency', 'description', 'current_level', 'target_level', 'learning_preference']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        skill = cleaned_data.get('skill')
        user = getattr(self.instance, 'user', None)
        
        if skill and user:
            existing = DesiredSkill.objects.filter(user=user, skill=skill).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing.exists():
                raise forms.ValidationError(f'You already want to learn {skill.name}.')
        
        return cleaned_data


class SkillSearchForm(forms.Form):
    """Form for searching skills"""
    query = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Search for skills...'}))
    category = forms.ModelChoiceField(queryset=SkillCategory.objects.filter(is_active=True), required=False, empty_label="All Categories") 