"""
Run this script to populate the database with sample practice texts.
python manage.py shell < populate_data.py
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'speech_therapy.settings')

import django
django.setup()

from practice.models import PracticeText

texts = [
    # Easy - Vowel Sounds
    {'title': 'Basic Vowel Sounds', 'content': 'A E I O U. Say each sound clearly. A E I O U.', 'category': 'vowels', 'difficulty': 'easy'},
    {'title': 'Vowel Words', 'content': 'Eat apple ice open umbrella', 'category': 'vowels', 'difficulty': 'easy'},

    # Easy - Simple Words
    {'title': 'Common Words 1', 'content': 'Hello my name is. I am here today.', 'category': 'words', 'difficulty': 'easy'},
    {'title': 'Family Words', 'content': 'Mother father sister brother family home love', 'category': 'words', 'difficulty': 'easy'},
    {'title': 'Colors', 'content': 'Red blue green yellow orange purple white black', 'category': 'words', 'difficulty': 'easy'},

    # Easy - Sentences
    {'title': 'Good Morning', 'content': 'Good morning. How are you? I am doing well today.', 'category': 'sentences', 'difficulty': 'easy'},
    {'title': 'The Weather', 'content': 'Today is a beautiful sunny day. The sky is clear and blue.', 'category': 'sentences', 'difficulty': 'easy'},
    {'title': 'My Day', 'content': 'I wake up early. I eat breakfast. Then I practice speaking.', 'category': 'sentences', 'difficulty': 'easy'},

    # Medium - Sentences
    {'title': 'Daily Routine', 'content': 'Every morning I brush my teeth, eat a healthy breakfast, and take a short walk in the garden.', 'category': 'sentences', 'difficulty': 'medium'},
    {'title': 'About My Family', 'content': 'My family is very important to me. We spend time together on weekends and enjoy cooking meals.', 'category': 'sentences', 'difficulty': 'medium'},
    {'title': 'The Park', 'content': 'The park near my house has tall trees and a small pond. Children play there every evening after school.', 'category': 'sentences', 'difficulty': 'medium'},
    {'title': 'My Goals', 'content': 'I practice speech therapy every day because I want to communicate better with my family and friends.', 'category': 'sentences', 'difficulty': 'medium'},

    # Medium - Paragraphs
    {'title': 'Morning Walk', 'content': 'I enjoy taking a morning walk in the fresh air. The birds sing beautiful songs and the flowers are blooming. Walking helps me feel healthy and happy.', 'category': 'paragraphs', 'difficulty': 'medium'},

    # Hard - Paragraphs
    {'title': 'The Importance of Practice', 'content': 'Regular speech practice is essential for improvement. Every day, I dedicate time to exercises that help strengthen my voice and improve my pronunciation. With patience and consistency, I am making meaningful progress.', 'category': 'paragraphs', 'difficulty': 'hard'},
    {'title': 'Communication', 'content': 'Effective communication is one of the most important skills in life. Whether speaking with family, friends, or doctors, being able to express yourself clearly builds confidence and strengthens relationships.', 'category': 'paragraphs', 'difficulty': 'hard'},

    # Consonant sounds
    {'title': 'P and B Sounds', 'content': 'Peter picked a pot of pepper. Bob bought big blue balloons.', 'category': 'consonants', 'difficulty': 'medium'},
    {'title': 'S and Sh Sounds', 'content': 'She sells sea shells by the seashore. Six silly snakes sat in the sun.', 'category': 'consonants', 'difficulty': 'hard'},

    # Tongue twisters (advanced)
    {'title': 'Red Lorry', 'content': 'Red lorry yellow lorry. Red lorry yellow lorry. Red lorry yellow lorry.', 'category': 'tongue_twisters', 'difficulty': 'hard'},
    {'title': 'Betty Botter', 'content': 'Betty Botter bought some butter. But she said the butter is bitter. If I put it in my batter it will make my batter bitter.', 'category': 'tongue_twisters', 'difficulty': 'hard'},
]

created = 0
for t in texts:
    obj, c = PracticeText.objects.get_or_create(title=t['title'], defaults=t)
    if c:
        created += 1

print(f"✅ Created {created} practice texts. Total: {PracticeText.objects.count()}")
