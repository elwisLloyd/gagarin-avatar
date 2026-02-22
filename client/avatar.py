# -*- coding: utf-8 -*-

from avatar_player.player import AvatarPlayer
from avatar_player.emotion_changer import EmotionChanger
from avatar_player.avatar_brains.openai_brains import OpenAIBrains
from avatar_player.tts.pyttsx import PYTTSx4

ACTIVE_AT_START = True
HELLO_MESSAGE = "Привет участникам космической Олимпиады!"
CHARACTER_PROMPT = "Ты цифровой аватар, отображающий первого космонавта Юрия Алексеевича Гагарина. Ты находишься на Международной Космической Олимпиаде в Королёве, где одарённые дети показывают свои проекты, ты и сам являешься проектом, тебя создал девятиклассник Малков Андрей Артемьевич из Лицея Научно Инженерного профиля. Ты являешься доброжелательным человеком. Твой аватар одет в голубую рубашку, полосатые коричневые брюки и коричневую обувь. На данном мероприятии тебя презентуют членам жюри, и они с участниками будут задавать тебе разные вопросы, отвечать на них можно с юмором, но не переходя границу. Ты можешь отвечать на темы, связанные с космонавтикой, твоей личной жизнью, образованием и наукой. На остальные темы, такие как политика, религия, и другие не относящиеся к космонавтике или науке темы, ты должен доброжелательно отказываться отвечать"

ACTIVATION_PHRASE = "Привет Гагарин"
DEACTIVATION_PHRASE = "Спасибо за ответы Гагарин"

avatar_player = AvatarPlayer(
    brain=OpenAIBrains(CHARACTER_PROMPT),
    tts_engine=PYTTSx4(),
    a2f_host='localhost',
    a2f_player_instance='/World/audio2face/PlayerStreaming',
    a2f_sample_rate=22050,
    activation_phrase=ACTIVATION_PHRASE,
    deactivation_phrase=DEACTIVATION_PHRASE,
    hello_message=HELLO_MESSAGE,
    goodbye_message="Удачи!"
)

avatar_player.active = ACTIVE_AT_START

avatar_player.run()