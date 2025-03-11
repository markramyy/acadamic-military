from django.core.management.base import BaseCommand

from users.models import User
from faculties.models import Faculty
from researches.models import Research


class Command(BaseCommand):
    help = 'Load mock data for faculties and researches'

    def handle(self, *args, **kwargs):

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@admin.com',
                password='admin',
            )
            self.stdout.write(self.style.SUCCESS('Created superuser'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))

        # Create faculties
        faculties = [
            {'name': 'كلية الطب', 'code': 'MED'},
            {'name': 'كلية العلوم', 'code': 'SCI'},
            {'name': 'كلية الصيدلة', 'code': 'PHARM'},
            {'name': 'كلية الهندسة', 'code': 'ENG'},
            {'name': 'كلية الحاسبات والمعلومات', 'code': 'CS'},
            {'name': 'كلية طب الاسنان', 'code': 'DENT'},
            {'name': 'كلية التجارة', 'code': 'COM'},
            {'name': 'كلية الالسن', 'code': 'LANG'},
            {'name': 'كلية التربية', 'code': 'EDU'},
            {'name': 'كلية الحقوق', 'code': 'LAW'},
            {'name': 'كلية الزراعة', 'code': 'AGR'},
            {'name': 'كلية الآداب', 'code': 'ARTS'},
            {'name': 'كلية الدراسات العليا والبحوث البيئية', 'code': 'ENV'},
            {'name': 'كلية الاثار', 'code': 'ARCH'},
            {'name': 'كلية الطب البيطري', 'code': 'VET'},
            {'name': 'كلية الإعلام', 'code': 'MEDIA'},
        ]

        for faculty_data in faculties:
            Faculty.objects.get_or_create(
                name=faculty_data['name'],
                code=faculty_data['code']
            )

        self.stdout.write(self.style.SUCCESS(f'Created {len(faculties)} faculties'))
