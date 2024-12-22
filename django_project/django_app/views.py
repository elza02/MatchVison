from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from .models import Team, Competition, Match, TopScorer, Player
from .serializers import (
    TeamSerializer,
    CompetitionSerializer,
    MatchSerializer,
    TopScorerSerializer,
    PlayerSerializer,
    TeamAnalyticsSerializer,
    CompetitionAnalyticsSerializer,
    MatchAnalyticsSerializer,
    PlayerAnalyticsSerializer
)
import django.db.models
from django.db.models import Sum, Count, Avg, F, Q
from django.db import connection

class DashboardStatsView(APIView):
    def get(self, request):
        try:
            # Get total counts only
            total_teams = Team.objects.count()
            total_matches = Match.objects.count()
            total_players = Player.objects.count()

            response_data = {
                "total_teams": total_teams,
                "total_matches": total_matches,
                "total_players": total_players
            }

            print("Stats response data:", response_data)
            return Response(response_data)
        except Exception as e:
            print(f"Error in DashboardStatsView: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardMatchesView(APIView):
    def get(self, request):
        try:
            recent_matches = Match.objects.select_related(
                'home_team', 'away_team', 'competition'
            ).order_by('-match_date')[:5]

            response_data = MatchSerializer(recent_matches, many=True).data
            print(f"Matches response data: {len(response_data)} matches")
            return Response(response_data)
        except Exception as e:
            print(f"Error in DashboardMatchesView: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DashboardScorersView(APIView):
    def get(self, request):
        try:
            top_scorers = TopScorer.objects.select_related(
                'player', 'player__team', 'competition'
            ).filter(
                player__isnull=False,
                goals__gt=0
            ).order_by('-goals')[:10]

            response_data = TopScorerSerializer(top_scorers, many=True).data
            print(f"Scorers response data: {len(response_data)} scorers")
            return Response(response_data)
        except Exception as e:
            print(f"Error in DashboardScorersView: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MatchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class MatchListView(APIView):
    pagination_class = MatchPagination

    def get(self, request):
        try:
            # Get query parameters
            status = request.query_params.get('status')
            competition = request.query_params.get('competition')
            team = request.query_params.get('team')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Start with all matches
            matches = Match.objects.all().order_by('-match_date')
            
            # Apply filters
            if status:
                matches = matches.filter(status=status)
            if competition:
                matches = matches.filter(competition_id=competition)
            if team:
                matches = matches.filter(Q(home_team_id=team) | Q(away_team_id=team))
            if date_from:
                matches = matches.filter(match_date__gte=date_from)
            if date_to:
                matches = matches.filter(match_date__lte=date_to)

            # Get paginator
            paginator = self.pagination_class()
            paginated_matches = paginator.paginate_queryset(matches, request)
            
            # Serialize the paginated data
            serializer = MatchSerializer(paginated_matches, many=True)
            
            # Return paginated response
            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class MatchDetailView(generics.RetrieveAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

class TeamListView(generics.ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class TeamDetailView(generics.RetrieveAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class PlayerListView(generics.ListAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class PlayerDetailView(generics.RetrieveAPIView):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class CompetitionListView(generics.ListAPIView):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

class CompetitionDetailView(generics.RetrieveAPIView):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

class MatchPredictionsView(APIView):
    def get(self, request):
        match_id = request.query_params.get('match_id')
        # Mocked predictions; replace with actual logic
        predictions = {
            "match_id": match_id,
            "home_win_probability": 0.45,
            "draw_probability": 0.30,
            "away_win_probability": 0.25,
        }
        return Response(predictions)

class CompetitionAnalyticsView(APIView):
    def get(self, request, competition_id):
        try:
            competition = Competition.objects.get(id=competition_id)
            serializer = CompetitionAnalyticsSerializer(competition)
            return Response(serializer.data)
        except Competition.DoesNotExist:
            return Response(
                {"error": "Competition not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class TeamAnalyticsView(APIView):
    def get(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id)
            serializer = TeamAnalyticsSerializer(team)
            return Response(serializer.data)
        except Team.DoesNotExist:
            return Response(
                {"error": "Team not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class MatchAnalyticsView(APIView):
    def get(self, request, match_id):
        try:
            match = Match.objects.get(id=match_id)
            serializer = MatchAnalyticsSerializer(match)
            return Response(serializer.data)
        except Match.DoesNotExist:
            return Response(
                {"error": "Match not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class PlayerAnalyticsView(APIView):
    def get(self, request, player_id):
        try:
            player = Player.objects.get(id=player_id)
            serializer = PlayerAnalyticsSerializer(player)
            return Response(serializer.data)
        except Player.DoesNotExist:
            return Response(
                {"error": "Player not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class TeamComparisonView(APIView):
    def get(self, request, team1_id, team2_id):
        try:
            team1 = Team.objects.get(id=team1_id)
            team2 = Team.objects.get(id=team2_id)
            
            # Head-to-head matches
            h2h_matches = Match.objects.filter(
                Q(home_team=team1, away_team=team2) |
                Q(home_team=team2, away_team=team1)
            ).order_by('-match_date')
            
            # Calculate head-to-head stats
            team1_wins = 0
            team2_wins = 0
            draws = 0
            
            for match in h2h_matches:
                if match.home_team_score > match.away_team_score:
                    if match.home_team == team1:
                        team1_wins += 1
                    else:
                        team2_wins += 1
                elif match.home_team_score < match.away_team_score:
                    if match.away_team == team1:
                        team1_wins += 1
                    else:
                        team2_wins += 1
                else:
                    draws += 1
            
            # Get recent form for both teams
            team1_form = TeamAnalyticsSerializer().get_form_analysis(team1)
            team2_form = TeamAnalyticsSerializer().get_form_analysis(team2)
            
            # Get top scorers for both teams
            team1_scorers = TopScorer.objects.filter(team=team1).order_by('-goals')[:5]
            team2_scorers = TopScorer.objects.filter(team=team2).order_by('-goals')[:5]
            
            return Response({
                'head_to_head': {
                    'total_matches': len(h2h_matches),
                    f'{team1.name}_wins': team1_wins,
                    f'{team2.name}_wins': team2_wins,
                    'draws': draws,
                    'recent_matches': MatchSerializer(h2h_matches[:5], many=True).data
                },
                'team_comparison': {
                    team1.name: {
                        'form': team1_form,
                        'top_scorers': [
                            {
                                'name': scorer.player.name,
                                'goals': scorer.goals,
                                'assists': scorer.assists
                            } for scorer in team1_scorers
                        ]
                    },
                    team2.name: {
                        'form': team2_form,
                        'top_scorers': [
                            {
                                'name': scorer.player.name,
                                'goals': scorer.goals,
                                'assists': scorer.assists
                            } for scorer in team2_scorers
                        ]
                    }
                }
            })
        except Team.DoesNotExist:
            return Response(
                {"error": "One or both teams not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )