from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Task
from .serializers import TaskSerializer, RegisterSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


#Register API
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={201: "User created"}
    )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "User created"})
        return Response(serializer.errors, status=400)


#Task List + Create
class TaskListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all tasks (creator or assignee)",
        security=[{"Bearer": []}]
    )

    def get(self, request):
        tasks = Task.objects.filter(
            Q(creator=request.user) | Q(assignee=request.user)
        )
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    @swagger_auto_schema(
        request_body=TaskSerializer,
        operation_description="Create a new task",
        security=[{"Bearer": []}]
    )

    def post(self, request):
        data = request.data
        serializer = TaskSerializer(data=data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
#Task Detail (Update + Delete)
class TaskDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    task_id_param = openapi.Parameter(
        'pk',
        openapi.IN_PATH,
        description="Task ID",
        type=openapi.TYPE_INTEGER
    )


    def get_object(self, pk, user):
        query = Q(creator=user) | Q(assignee=user)
        return get_object_or_404(Task, query, pk=pk)
    
    @swagger_auto_schema(
        manual_parameters=[task_id_param],
        security=[{"Bearer": []}]
    )

    def get(self, request, pk):
        task = self.get_object(pk, request.user)
        return Response(TaskSerializer(task).data)
    
    @swagger_auto_schema(
        manual_parameters=[task_id_param],
        request_body=TaskSerializer,
        security=[{"Bearer": []}]
    )

    def put(self, request, pk):
        task = self.get_object(pk, request.user)
        user = request.user

        data = request.data

        # Assignee → only status
        if task.assignee == user:
            task.status = data.get('status', task.status)

        # Creator → everything except status
        elif task.creator == user:
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            task.due_date = data.get('due_date', task.due_date)

        task.save()
        return Response(TaskSerializer(task).data)
    
    @swagger_auto_schema(
        manual_parameters=[task_id_param],
        security=[{"Bearer": []}]
    )

    def delete(self, request, pk):
        task = self.get_object(pk, request.user)
        task.delete()
        return Response({"msg": "Deleted"})
    
