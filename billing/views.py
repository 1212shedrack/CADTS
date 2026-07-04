# billing/views.py
# Phase 8 — Full billing API views

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# from rest_framework import status

from accounts.permissions import IsAdminRole
from .models import Billing
from .serializers import BillingSerializer


# USER — My Bills
class UserBillingListView(APIView):
    """
    GET /api/billing/my/
    Returns all billing records for the authenticated user's completed trips.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "user":
            return Response({"error": "Only users can access this."},
                            status=403)

        bills = Billing.objects.filter(
            request__user=request.user
        ).select_related(
            "request", "request__user", "request__ambulance"
        ).order_by("-created_at")

        serializer = BillingSerializer(bills, many=True)
        return Response(serializer.data)


class UserBillingDetailView(APIView):
    """
    GET /api/billing/<id>/
    Returns a single billing record (user must own it).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            bill = Billing.objects.select_related(
                "request", "request__user", "request__ambulance"
            ).get(pk=pk)
        except Billing.DoesNotExist:
            return Response({"error": "Bill not found."}, status=404)

        if request.user.role != "admin" and bill.request.user != request.user:
            return Response({"error": "Not authorized."}, status=403)

        return Response(BillingSerializer(bill).data)


# ADMIN — All Bills + Summary Stats


class AdminBillingListView(APIView):
    """
    GET /api/billing/admin/
    Returns all billing records (admin only).
    Supports ?limit=N and ?ambulance=<id> filters.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        qs = Billing.objects.select_related(
            "request", "request__user", "request__ambulance"
        ).order_by("-created_at")

        # Optional filters
        ambulance_id = request.query_params.get("ambulance")
        limit = request.query_params.get("limit")
        if ambulance_id:
            qs = qs.filter(request__ambulance_id=ambulance_id)
        if limit:
            try:
                qs = qs[:int(limit)]
            except ValueError:
                pass

        return Response(BillingSerializer(qs, many=True).data)


class AdminBillingStatsView(APIView):
    """
    GET /api/billing/admin/stats/
    Returns aggregate billing statistics for the admin dashboard.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        from django.db.models import Sum, Count, Avg
        stats = Billing.objects.aggregate(
            total_revenue=Sum("total_cost"),
            total_trips=Count("id"),
            total_km=Sum("distance_km"),
            avg_cost=Avg("total_cost"),
        )
        return Response({
            "total_revenue": float(stats["total_revenue"] or 0),
            "total_trips": stats["total_trips"] or 0,
            "total_km": float(stats["total_km"] or 0),
            "avg_cost": float(stats["avg_cost"] or 0),
        })
