

# Create your views here.
from rest_framework import generics, permissions
from .models import Question, Test, Option
from .serializers import QuestionSerializer, TestSerializer, TestCreateSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import json
from django.conf import settings
import os
# 1) Questions GET
class QuestionListView(generics.ListAPIView):
    queryset = Question.objects.prefetch_related('options').all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

# 2) Test Create
class TestCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TestCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user

        from licenses.models import TestInvitation
        from django.db.models import Sum
        reserved = TestInvitation.objects.filter(
            sender=user, status='PENDING'
        ).aggregate(total=Sum('credit_count'))['total'] or 0
        available = user.active_test_count - reserved

        if available > 0:
            user.active_test_count -= 1
            user.save()
        else:
            return Response(
                {'message': 'No available test credits (some may be reserved for invitations).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        test = serializer.save()
        
        return Response({'test_id': test.id}, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        # Browser açanda text olaraq nümunəni göstəririk
        example = {
            "answers": [1, 2, 3]
        }
        return Response(
            {
                "message": "POST üçün nümunə JSON",
                "example": example
            },
            status=status.HTTP_200_OK
        )

# 3) List tests for user
class UserTestListView(generics.ListAPIView):
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Test.objects.filter(user=self.request.user).order_by('-created_at')
    

# 4) Test detail with answers
class TestDetailView(generics.RetrieveAPIView):
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Test.objects.all()


from .models import PersonalityType
from .serializers import PersonalityTypeDetailSerializer

# List API (sadəcə id və name də ola bilər)
class PersonalityTypeListView(generics.ListAPIView):
    queryset = PersonalityType.objects.all()
    serializer_class = PersonalityTypeDetailSerializer  # nested info ilə

# Detail API (lookup by code)
class PersonalityTypeDetailView(generics.RetrieveAPIView):
    queryset = PersonalityType.objects.all()
    serializer_class = PersonalityTypeDetailSerializer
    lookup_field = 'code'

class LoadQuestionsAPIView(APIView):
    """
    API çağırıldıqda mövcud sualları sil və questions.json-dan DB-yə doldur.
    """

    def post(self, request):
        # 1️⃣ Mövcud datanı sil
        Option.objects.all().delete()
        Question.objects.all().delete()

        # 2️⃣ JSON faylını oxu
        file_path = os.path.join(settings.BASE_DIR, "data", "questions.json")
        with open(file_path, "r", encoding="utf-8") as f:
            questions_data = json.load(f)

        # 3️⃣ DB-yə yaz
        for q in questions_data:
            # Question obyektini əvvəl save et
            question = Question(
                text=q["question"],
                dimension=q.get("dimension", ""),
                type=q.get("type", "likert")
            )
            question.save()  # FK üçün commit

            # Option-ları bulk_create ilə əlavə et
            options_to_create = [
                Option(
                    question=question,
                    text=opt["text"],
                    value=opt["value"]
                )
                for opt in q.get("options", [])
            ]
            Option.objects.bulk_create(options_to_create)

        return Response(
            {"message": "Questions loaded successfully"},
            status=status.HTTP_201_CREATED
        )
    


from .models import PersonalityType
from django.db import transaction
class LoadPersonalityTypesAPIView(APIView):
    """
    API çağırıldıqda mövcud personality types datalarını silir və
    personalityTypes.json faylından DB-yə yenidən doldurur.
    Modeltranslation field-ləri bütün dillər üzrə yazılır.
    """

    def post(self, request):
        # Bütün dilləri götür
        LANGS = [lang[0] for lang in settings.LANGUAGES]

        # JSON path
        file_path = os.path.join(settings.BASE_DIR, "data", "personalityTypes.json")

        with open(file_path, "r", encoding="utf-8") as f:
            types_data = json.load(f)

        with transaction.atomic():
            # 1️⃣ Köhnə datanı sil
            PersonalityType.objects.all().delete()

            # Helper → translatable field doldurur
            def build_i18n_defaults(details):
                defaults = {}

                # Text Fields Mapping
                text_fields_map = {
                    "name": details.get("name", ""),
                    "summary": details.get("summary", ""),
                    "workplace_personality": details.get("workplacePersonality", ""),
                    "working_with_team": details.get("workingWithTeam", ""),
                    "communicating_with_others": details.get("communicatingWithOthers", ""),
                    "managing_conflict": details.get("managingConflict", ""),
                    "taking_the_lead": details.get("takingTheLead", ""),
                    "getting_things_done": details.get("gettingThingsDone", ""),
                    "growth_and_development": details.get("growthAndDevelopment", ""),
                    "coping_with_stress": details.get("copingWithStress", ""),
                    "achieving_success": details.get("achievingSuccess", ""),
                    "making_decisions": details.get("makingDecisions", ""),
                }
                
                # List Fields Mapping (JSONFields)
                list_fields_map = {
                    "key_motivators": details.get("keyMotivators", []),
                    "ideal_work_environments": details.get("idealWorkEnvironment", []),
                    "core_values": details.get("coreValues", []),
                    "preferred_work_tasks": details.get("preferredWorkTasks", []),
                    "contributions_to_organization": details.get("contributionsToOrganization", []),
                    "team_helps": details.get("teamHelp", []),
                    "team_irritates": details.get("teamIrritate", []),
                    "team_action_steps": details.get("teamActionSteps", []),
                    "communication_strengths": details.get("communicationStrengths", []),
                    "communication_misunderstanding": details.get("communicationMisunderstanding", []),
                    "communication_action_steps": details.get("communicationActionSteps", []),
                    "conflict_help": details.get("conflictHelp", []),
                    "conflict_triggered_by": details.get("conflictTriggeredBy", []),
                    "conflict_irritate": details.get("conflictIrritate", []),
                    "conflict_action_steps": details.get("conflictActionSteps", []),
                    "inspire_others": details.get("inspireOthers", []),
                    "make_things_happen": details.get("makeThingsHappen", []),
                    "leadership_development": details.get("leadershipDevelopment", []),
                    "decision_strengths": details.get("decisionStrengths", []),
                    "decision_challenges": details.get("decisionChallenges", []),
                    "decision_action_steps": details.get("decisionActionSteps", []),
                    "tasks_help": details.get("tasksHelp", []),
                    "tasks_irritate": details.get("tasksIrritate", []),
                    "tasks_action_steps": details.get("tasksActionSteps", []),
                    "learning_improved": details.get("learningImproved", []),
                    "learning_hindered": details.get("learningHindered", []),
                    "how_you_view_change": details.get("howYouViewChange", []),
                    "opportunities_for_growth": details.get("opportunitiesForGrowth", []),
                    "stress_triggers": details.get("stressTriggers", []),
                    "best_stress_response": details.get("bestStressResponse", []),
                    "others_help_stress": details.get("othersHelpStress", []),
                    "worst_stress_response": details.get("worstStressResponse", []),
                    "others_worsen_stress": details.get("othersWorsenStress", []),
                    "potential_problems": details.get("potentialProblems", []),
                    "suggestions_do": details.get("suggestionsDo", []),
                    "suggestions_dont": details.get("suggestionsDont", []),
                }

                # Combine maps
                fields_map = {**text_fields_map, **list_fields_map}

                for field, value in fields_map.items():
                    # Əgər modeldə translation varsa yaz
                    for lang in LANGS:
                        field_name = f"{field}_{lang}"
                        if hasattr(PersonalityType, field_name):
                            defaults[field_name] = value

                    # Default field də doldurulsun (optional but good for fallback)
                    if hasattr(PersonalityType, field):
                        defaults[field] = value

                return defaults

            # 2️⃣ DB-yə yaz
            for code, details in types_data.items():
                PersonalityType.objects.update_or_create(
                    code=code,
                    defaults=build_i18n_defaults(details),
                )

        return Response(
            {"message": "Personality types loaded successfully"},
            status=status.HTTP_201_CREATED,
        )