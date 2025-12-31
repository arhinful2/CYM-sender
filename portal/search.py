from django.db.models import Q
from members.models import Member
from fuzzywuzzy import fuzz
import re

class AdvancedMemberSearch:
    def __init__(self):
        self.search_fields = [
            'first_name',
            'last_name',
            'middle_name',
            'phone_number',
            'email',
            'address',
            'city',
            'state',
            'occupation',
            'school',
            'talents',
            'spiritual_gifts',
        ]
    
    def search(self, query, filters=None):
        """
        Advanced search with fuzzy matching and filters
        """
        # Basic search
        q_objects = Q()
        for field in self.search_fields:
            q_objects |= Q(**{f"{field}__icontains": query})
        
        members = Member.objects.filter(q_objects).distinct()
        
        # Apply filters
        if filters:
            members = self.apply_filters(members, filters)
        
        # Score results based on relevance
        scored_results = []
        for member in members:
            score = self.calculate_relevance_score(member, query)
            scored_results.append({
                'member': member,
                'score': score
            })
        
        # Sort by relevance
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        return [item['member'] for item in scored_results]
    
    def calculate_relevance_score(self, member, query):
        """
        Calculate relevance score using fuzzy matching
        """
        score = 0
        
        # Check exact matches
        if query.lower() in member.first_name.lower():
            score += 100
        if query.lower() in member.last_name.lower():
            score += 100
        if query in str(member.phone_number):
            score += 100
        if query.lower() in member.email.lower():
            score += 100
        
        # Fuzzy matching for names
        full_name = f"{member.first_name} {member.last_name}"
        name_score = fuzz.partial_ratio(query.lower(), full_name.lower())
        score += name_score / 2
        
        # Phone number matching (partial)
        if query.replace(' ', '').replace('-', '').isdigit():
            phone_digits = str(member.phone_number).replace(' ', '').replace('-', '').replace('+', '')
            if query.replace(' ', '').replace('-', '') in phone_digits:
                score += 50
        
        return score
    
    def apply_filters(self, members, filters):
        """
        Apply advanced filters to search results
        """
        if filters.get('status'):
            members = members.filter(status=filters['status'])
        
        if filters.get('gender'):
            members = members.filter(gender=filters['gender'])
        
        if filters.get('min_age'):
            from datetime import date
            min_birth_year = date.today().year - int(filters['min_age'])
            members = members.filter(date_of_birth__year__lte=min_birth_year)
        
        if filters.get('max_age'):
            from datetime import date
            max_birth_year = date.today().year - int(filters['max_age'])
            members = members.filter(date_of_birth__year__gte=max_birth_year)
        
        if filters.get('department'):
            members = members.filter(department__icontains=filters['department'])
        
        if filters.get('date_joined_start'):
            members = members.filter(date_joined__gte=filters['date_joined_start'])
        
        if filters.get('date_joined_end'):
            members = members.filter(date_joined__lte=filters['date_joined_end'])
        
        return members
    
    def get_search_suggestions(self, query):
        """
        Get search suggestions based on partial query
        """
        suggestions = []
        
        # Name suggestions
        name_matches = Member.objects.filter(
            Q(first_name__istartswith=query) |
            Q(last_name__istartswith=query)
        )[:5]
        
        for member in name_matches:
            suggestions.append({
                'type': 'name',
                'text': member.full_name(),
                'member_id': member.id
            })
        
        # Phone suggestions
        if any(char.isdigit() for char in query):
            phone_matches = Member.objects.filter(
                phone_number__icontains=query
            )[:3]
            
            for member in phone_matches:
                suggestions.append({
                    'type': 'phone',
                    'text': f"{member.full_name()} - {member.phone_number}",
                    'member_id': member.id
                })
        
        return suggestions
    