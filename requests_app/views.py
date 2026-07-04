# requests_app/views.py
# Full request workflow: create, accept, reject, trip lifecycle, cancel

import math
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsAdminRole, IsDriverRole, IsUserRole
from ambulances.models import Ambulance
from billing.models import Billing
from .models import Request
from .serializers import RequestSerializer, RequestCreateSerializer


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance in km between two GPS points."""
    R    = 6371
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlam = math.radians(float(lon2) - float(lon1))
    a    = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────────────────
# USER — Create & List My Requests
# ─────────────────────────────────────────────────────────────────────────────
class UserRequestListCreateView(APIView):
    """
    GET  /api/requests/my/  — User: list own requests
    POST /api/requests/     — User: create new request
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "user":
            return Response({"error": "Only users can access this."}, status=403)
        qs = Request.objects.filter(user=request.user).order_by("-created_at")
        return Response(RequestSerializer(qs, many=True).data)

    def post(self, request):
        if request.user.role != "user":
            return Response({"error": "Only users can request ambulances."}, status=403)

        serializer = RequestCreateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            req = serializer.save()
            return Response(RequestSerializer(req).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRequestDetailView(APIView):
    """GET /api/requests/<id>/ — User or Driver or Admin: get request detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            req = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            return Response({"error": "Not found."}, status=404)

        # Users can only see own requests
        if request.user.role == "user" and req.user != request.user:
            return Response({"error": "Forbidden."}, status=403)

        return Response(RequestSerializer(req).data)


class UserCancelRequestView(APIView):
    """POST /api/requests/<id>/cancel/ — User: cancel a pending request."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            req = Request.objects.get(pk=pk, user=request.user)
        except Request.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)

        if req.status not in [Request.Status.PENDING]:
            return Response(
                {"error": f"Cannot cancel a request with status '{req.status}'."},
                status=400
            )

        with transaction.atomic():
            if req.ambulance:
                req.ambulance.status = Ambulance.Status.AVAILABLE
                req.ambulance.save()
            req.status = Request.Status.CANCELLED
            req.save()

        return Response({"message": "Request cancelled."})


# ─────────────────────────────────────────────────────────────────────────────
# DRIVER — View, Accept, Reject, Lifecycle
# ─────────────────────────────────────────────────────────────────────────────
class DriverRequestListView(APIView):
    """
    GET /api/requests/driver/  — Driver: list all requests assigned to their ambulance
    GET /api/requests/driver/?status=pending — filter
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["driver", "admin"]:
            return Response({"error": "Forbidden."}, status=403)

        try:
            ambulance = request.user.ambulance
        except Exception:
            return Response({"error": "No ambulance assigned to you."}, status=404)

        qs = Request.objects.filter(ambulance=ambulance).order_by("-created_at")

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return Response(RequestSerializer(qs, many=True).data)


class DriverCurrentRequestView(APIView):
    """GET /api/requests/driver/current/ — Driver: get current active request."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "driver":
            return Response({"error": "Forbidden."}, status=403)
        try:
            ambulance = request.user.ambulance
        except Exception:
            return Response({"error": "No ambulance assigned."}, status=404)

        active_statuses = [
            Request.Status.PENDING,
            Request.Status.ACCEPTED,
            Request.Status.ARRIVED,
            Request.Status.PATIENT_PICKED,
        ]
        req = Request.objects.filter(
            ambulance=ambulance,
            status__in=active_statuses
        ).order_by("-created_at").first()

        if not req:
            return Response({"detail": "No active request."}, status=204)

        return Response(RequestSerializer(req).data)


class DriverAcceptRequestView(APIView):
    """POST /api/requests/<id>/accept/ — Driver accepts a pending request."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "driver":
            return Response({"error": "Only drivers can accept requests."}, status=403)

        try:
            req = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)

        if req.status != Request.Status.PENDING:
            return Response({"error": f"Request is already '{req.status}'."}, status=400)

        # Verify this is the driver's ambulance
        try:
            ambulance = request.user.ambulance
        except Exception:
            return Response({"error": "No ambulance assigned to you."}, status=403)

        if req.ambulance and req.ambulance != ambulance:
            return Response({"error": "This request is not for your ambulance."}, status=403)

        req.status = Request.Status.ACCEPTED
        req.save()

        return Response({"message": "Request accepted! Head to pickup location.", "request": RequestSerializer(req).data})


class DriverRejectRequestView(APIView):
    """POST /api/requests/<id>/reject/ — Driver rejects a pending request."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "driver":
            return Response({"error": "Only drivers can reject requests."}, status=403)

        try:
            req = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)

        if req.status != Request.Status.PENDING:
            return Response({"error": f"Request is '{req.status}', cannot reject."}, status=400)

        with transaction.atomic():
            # Free ambulance
            if req.ambulance:
                req.ambulance.status = Ambulance.Status.AVAILABLE
                req.ambulance.save()
            req.status = Request.Status.REJECTED
            req.save()

        return Response({"message": "Request rejected. Ambulance is now available."})


class DriverUpdateStatusView(APIView):
    """
    POST /api/requests/<id>/status/ — Driver advances the request status.
    Body: { "status": "arrived" | "patient_picked" | "completed" }
    """
    permission_classes = [IsAuthenticated]

    ALLOWED_TRANSITIONS = {
        Request.Status.ACCEPTED:       [Request.Status.ARRIVED],
        Request.Status.ARRIVED:        [Request.Status.PATIENT_PICKED],
        Request.Status.PATIENT_PICKED: [Request.Status.COMPLETED],
    }

    def post(self, request, pk):
        if request.user.role != "driver":
            return Response({"error": "Only drivers can update request status."}, status=403)

        try:
            req = Request.objects.get(pk=pk)
        except Request.DoesNotExist:
            return Response({"error": "Request not found."}, status=404)

        new_status = request.data.get("status")
        if not new_status:
            return Response({"error": "'status' field is required."}, status=400)

        allowed = self.ALLOWED_TRANSITIONS.get(req.status, [])
        if new_status not in allowed:
            return Response(
                {"error": f"Cannot transition from '{req.status}' to '{new_status}'."},
                status=400
            )

        with transaction.atomic():
            req.status = new_status
            req.save()

            # When trip is completed: free ambulance + create billing
            if new_status == Request.Status.COMPLETED:
                if req.ambulance:
                    req.ambulance.status = Ambulance.Status.AVAILABLE
                    req.ambulance.save()

                # Auto-billing: calculate distance
                distance_km = 0
                if (req.pickup_latitude and req.pickup_longitude
                        and req.ambulance and req.ambulance.latitude and req.ambulance.longitude):
                    distance_km = haversine_km(
                        req.ambulance.latitude, req.ambulance.longitude,
                        req.pickup_latitude, req.pickup_longitude
                    )

                billing, _ = Billing.objects.get_or_create(request=req)
                billing.distance_km  = round(distance_km, 2)
                billing.base_fee     = 5000
                billing.price_per_km = 2000
                billing.calculate()

        status_labels = {
            "arrived":       "Arrived at pickup location!",
            "patient_picked":"Patient picked up! En route to hospital.",
            "completed":     "Trip completed! Billing generated.",
        }
        return Response({
            "message": status_labels.get(new_status, f"Status updated to '{new_status}'."),
            "request": RequestSerializer(req).data,
        })


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — All Requests
# ─────────────────────────────────────────────────────────────────────────────
class AdminRequestListView(APIView):
    """GET /api/requests/ — Admin: list all requests with optional filters."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = Request.objects.all().order_by("-created_at").select_related(
            "user", "ambulance"
        )
        # Filters
        status_f  = request.query_params.get("status")
        limit     = request.query_params.get("limit")
        if status_f:
            qs = qs.filter(status=status_f)
        if limit:
            qs = qs[:int(limit)]
        return Response(RequestSerializer(qs, many=True).data)
