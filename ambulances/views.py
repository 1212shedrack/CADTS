# ambulances/views.py
# API views + HTML page views for ambulance management

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from accounts.models import CustomUser
from accounts.permissions import IsAdminRole, IsDriverRole
from drivers.models import DriverProfile
from .models import Ambulance
from .serializers import AmbulanceSerializer, AmbulanceCreateSerializer, DriverChoiceSerializer


# ─────────────────────────────────────────────────────────────────────────────
# HTML PAGE VIEWS
# ─────────────────────────────────────────────────────────────────────────────
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')

def admin_users(request):
    return render(request, 'admin/users.html')

def admin_drivers(request):
    return render(request, 'admin/drivers.html')

def admin_ambulances(request):
    return render(request, 'admin/ambulances.html')

def admin_requests(request):
    return render(request, 'admin/requests.html')

def admin_reports(request):
    return render(request, 'admin/reports.html')

def admin_settings(request):
    return render(request, 'admin/settings.html')


# ─────────────────────────────────────────────────────────────────────────────
# AMBULANCE API VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class AmbulanceListCreateAPIView(APIView):
    """
    GET  /api/ambulances/        — List ambulances
                                   Users see only 'available'; Admin sees all.
    POST /api/ambulances/        — Admin: Register a new ambulance
    """
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get(self, request):
        role = request.user.role
        if role == "admin":
            ambulances = Ambulance.objects.all().select_related("driver")
        else:
            # Users and drivers see only available ambulances
            ambulances = Ambulance.objects.filter(
                status=Ambulance.Status.AVAILABLE
            ).select_related("driver")

        # Filter by status query param
        status_param = request.query_params.get("status")
        if status_param:
            ambulances = ambulances.filter(status=status_param)

        serializer = AmbulanceSerializer(ambulances, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AmbulanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            ambulance = serializer.save()
            return Response(
                AmbulanceSerializer(ambulance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AmbulanceDetailAPIView(APIView):
    """
    GET    /api/ambulances/<id>/  — Get ambulance detail
    PATCH  /api/ambulances/<id>/  — Admin: Edit ambulance
    DELETE /api/ambulances/<id>/  — Admin: Delete ambulance
    """
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def get_object(self, pk):
        try:
            return Ambulance.objects.select_related("driver").get(pk=pk)
        except Ambulance.DoesNotExist:
            return None

    def get(self, request, pk):
        ambulance = self.get_object(pk)
        if not ambulance:
            return Response({"error": "Ambulance not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AmbulanceSerializer(ambulance).data)

    def patch(self, request, pk):
        ambulance = self.get_object(pk)
        if not ambulance:
            return Response({"error": "Ambulance not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AmbulanceCreateSerializer(ambulance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(AmbulanceSerializer(ambulance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        ambulance = self.get_object(pk)
        if not ambulance:
            return Response({"error": "Ambulance not found."}, status=status.HTTP_404_NOT_FOUND)
        ambulance.delete()
        return Response({"message": "Ambulance deleted."}, status=status.HTTP_204_NO_CONTENT)


class AmbulanceAssignDriverAPIView(APIView):
    """POST /api/ambulances/<id>/assign/ — Admin assigns a driver to an ambulance."""
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        try:
            ambulance = Ambulance.objects.get(pk=pk)
        except Ambulance.DoesNotExist:
            return Response({"error": "Ambulance not found."}, status=status.HTTP_404_NOT_FOUND)

        driver_id = request.data.get("driver_id")
        if not driver_id:
            # Unassign
            ambulance.driver = None
            ambulance.status = Ambulance.Status.OFFLINE
            ambulance.save()
            return Response({"message": "Driver unassigned. Ambulance set to Offline."})

        try:
            driver = CustomUser.objects.get(pk=driver_id, role="driver", is_approved=True)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Driver not found or not approved."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check no other ambulance assigned to this driver
        if Ambulance.objects.filter(driver=driver).exclude(pk=pk).exists():
            return Response(
                {"error": "This driver is already assigned to another ambulance."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ambulance.driver = driver
        if ambulance.status == Ambulance.Status.OFFLINE:
            ambulance.status = Ambulance.Status.AVAILABLE
        ambulance.save()

        return Response({
            "message": f"Driver '{driver.full_name}' assigned to '{ambulance.ambulance_name}'.",
            "ambulance": AmbulanceSerializer(ambulance).data,
        })


class DriverMineAPIView(APIView):
    """GET /api/ambulances/mine/ — Driver gets their assigned ambulance."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            ambulance = Ambulance.objects.get(driver=request.user)
            return Response(AmbulanceSerializer(ambulance).data)
        except Ambulance.DoesNotExist:
            return Response({"error": "No ambulance assigned to you."}, status=status.HTTP_404_NOT_FOUND)


class DriverListAPIView(APIView):
    """GET /api/drivers/ — Admin: List all drivers with their profile info."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        drivers = CustomUser.objects.filter(role="driver").select_related("driver_profile")
        data = []
        for d in drivers:
            profile = getattr(d, "driver_profile", None)
            data.append({
                "id":             d.id,
                "full_name":      d.full_name,
                "email":          d.email,
                "phone":          d.phone,
                "is_approved":    d.is_approved,
                "is_active":      d.is_active,
                "license_number": profile.license_number if profile else "—",
                "status":         profile.status if profile else "—",
                "created_at":     d.created_at,
            })
        return Response(data)


class DriverApproveAPIView(APIView):
    """POST /api/drivers/<id>/approve/ — Admin approves or deactivates a driver."""
    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        try:
            driver = CustomUser.objects.get(pk=pk, role="driver")
        except CustomUser.DoesNotExist:
            return Response({"error": "Driver not found."}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get("action")  # "approve" | "deactivate" | "activate"
        if action == "approve":
            driver.is_approved = True
            driver.is_active   = True
            driver.save()
            return Response({"message": f"Driver '{driver.full_name}' approved."})
        elif action == "deactivate":
            driver.is_active = False
            driver.save()
            return Response({"message": f"Driver '{driver.full_name}' deactivated."})
        elif action == "activate":
            driver.is_active = True
            driver.save()
            return Response({"message": f"Driver '{driver.full_name}' activated."})
        else:
            return Response({"error": "Invalid action. Use 'approve', 'activate', or 'deactivate'."}, status=400)


class UserListAPIView(APIView):
    """GET /api/admin/users/ — Admin: List all users."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        users = CustomUser.objects.filter(role="user").order_by("-created_at")
        data = [{
            "id":         u.id,
            "full_name":  u.full_name,
            "email":      u.email,
            "phone":      u.phone,
            "is_active":  u.is_active,
            "created_at": u.created_at,
        } for u in users]
        return Response(data)


class DriverChoicesAPIView(APIView):
    """GET /api/drivers/choices/ — Admin: Get approved drivers without an ambulance (for dropdown)."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        # Drivers who are approved and not yet assigned to any ambulance
        assigned_ids = Ambulance.objects.exclude(driver=None).values_list("driver_id", flat=True)
        drivers = CustomUser.objects.filter(
            role="driver", is_approved=True
        ).exclude(id__in=assigned_ids)
        data = [{"id": d.id, "full_name": d.full_name, "email": d.email} for d in drivers]
        return Response(data)


class AdminStatsAPIView(APIView):
    """GET /api/admin/stats/ — Admin dashboard statistics."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        from billing.models import Billing

        total_users       = CustomUser.objects.filter(role="user").count()
        total_drivers     = CustomUser.objects.filter(role="driver").count()
        pending_drivers   = CustomUser.objects.filter(role="driver", is_approved=False).count()
        available_amb     = Ambulance.objects.filter(status="available").count()
        busy_amb          = Ambulance.objects.filter(status="busy").count()
        total_ambulances  = Ambulance.objects.count()

        try:
            from requests_app.models import Request
            total_requests = Request.objects.count()
        except Exception:
            total_requests = 0

        try:
            total_revenue = sum(
                b.total_cost for b in Billing.objects.all() if b.total_cost
            )
        except Exception:
            total_revenue = 0

        return Response({
            "total_users":           total_users,
            "total_drivers":         total_drivers,
            "pending_drivers":       pending_drivers,
            "available_ambulances":  available_amb,
            "busy_ambulances":       busy_amb,
            "total_ambulances":      total_ambulances,
            "total_requests":        total_requests,
            "total_revenue":         total_revenue,
        })
