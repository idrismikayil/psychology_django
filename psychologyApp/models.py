from django.db import models
from django.conf import settings

class Test(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tests')
    created_at = models.DateTimeField(auto_now=True)
    result_values = models.JSONField(null=True,blank=True)
    result = models.TextField(null=True,blank=True)

class Question(models.Model):
    text = models.TextField()
    dimension = models.CharField(max_length=10) 
    type = models.CharField(max_length=50, default='likert')  

    def __str__(self):
        return f"{self.text} - {self.text[:50]}"


class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    value = models.JSONField()  # E.g. {"E": 5, "I":1}

    def __str__(self):
        question_text = self.question.text[:20] if self.question else "NoQuestion"
        return f"{question_text} - {self.text}"


class Answer(models.Model):
    test = models.ForeignKey(Test, related_name='answers', on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    def __str__(self):
        try:
            if self.option and self.option.question:
                return str(self.option.question.text)
            elif self.option:
                return str(self.option.text)
            return "Empty Object"
        except Exception:
            return "Invalid Object"
    

class PersonalityType(models.Model):
    code = models.CharField(max_length=10, unique=True)  # INTJ, INTP
    file = models.FileField(upload_to='personality_types/', null=True, blank=True) 
    name = models.CharField(max_length=100)
    summary = models.TextField()
    workplace_personality = models.TextField()
    working_with_team = models.TextField()
    communicating_with_others = models.TextField()
    managing_conflict = models.TextField()
    taking_the_lead = models.TextField()
    getting_things_done = models.TextField()
    growth_and_development = models.TextField()
    coping_with_stress = models.TextField()
    achieving_success = models.TextField()
    making_decisions = models.TextField(null=True, blank=True) # New text field

    # JSON Fields for lists
    key_motivators = models.JSONField(default=list, blank=True)
    ideal_work_environments = models.JSONField(default=list, blank=True)
    core_values = models.JSONField(default=list, blank=True)
    preferred_work_tasks = models.JSONField(default=list, blank=True)
    contributions_to_organization = models.JSONField(default=list, blank=True)
    
    # Team
    team_helps = models.JSONField(default=list, blank=True)
    team_irritates = models.JSONField(default=list, blank=True)
    team_action_steps = models.JSONField(default=list, blank=True)
    
    # Communication
    communication_strengths = models.JSONField(default=list, blank=True)
    communication_misunderstanding = models.JSONField(default=list, blank=True)
    communication_action_steps = models.JSONField(default=list, blank=True)
    
    # Conflict
    conflict_help = models.JSONField(default=list, blank=True)
    conflict_triggered_by = models.JSONField(default=list, blank=True)
    conflict_irritate = models.JSONField(default=list, blank=True)
    conflict_action_steps = models.JSONField(default=list, blank=True)
    
    # Leadership
    inspire_others = models.JSONField(default=list, blank=True)
    make_things_happen = models.JSONField(default=list, blank=True)
    leadership_development = models.JSONField(default=list, blank=True)
    
    # Decisions
    decision_strengths = models.JSONField(default=list, blank=True)
    decision_challenges = models.JSONField(default=list, blank=True)
    decision_action_steps = models.JSONField(default=list, blank=True)
    
    # Tasks
    tasks_help = models.JSONField(default=list, blank=True)
    tasks_irritate = models.JSONField(default=list, blank=True)
    tasks_action_steps = models.JSONField(default=list, blank=True)
    
    # Learning/Growth
    learning_improved = models.JSONField(default=list, blank=True)
    learning_hindered = models.JSONField(default=list, blank=True)
    how_you_view_change = models.JSONField(default=list, blank=True)
    opportunities_for_growth = models.JSONField(default=list, blank=True)
    
    # Stress
    stress_triggers = models.JSONField(default=list, blank=True)
    best_stress_response = models.JSONField(default=list, blank=True)
    others_help_stress = models.JSONField(default=list, blank=True)
    worst_stress_response = models.JSONField(default=list, blank=True)
    others_worsen_stress = models.JSONField(default=list, blank=True)
    
    # Success
    potential_problems = models.JSONField(default=list, blank=True)
    suggestions_do = models.JSONField(default=list, blank=True)
    suggestions_dont = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.code

