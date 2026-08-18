/* ==========================================================================
   MAFIA GAME - MULTI-LANGUAGE SYSTEM (AZ, RU, EN)
   ========================================================================== */

const TRANSLATIONS = {
    az: {
        app_title: "Mafiya Onlayn",
        brand_title_1: "MAFIYA",
        brand_title_2: "OYUNU",
        brand_subtitle: "Şəhər yatır... Mafiya oyanır",
        tab_join: "Oyuna qoşul",
        tab_host: "Aparıcı",
        label_nickname: "Adınız / Ləqəbiniz",
        placeholder_nickname: "Məs: Don Karleone",
        label_room_code: "Otaq kodu",
        placeholder_room_code: "5 rəqəmli kod (məs: 49201)",
        btn_join: "Qoşul",
        host_desc: "Aparıcı olmaq, rolların balansını tənzimləmək və oyunu real vaxtda idarə etmək üçün oyun otağı yaradın.",
        btn_create_room: "Yeni otaq yarat",
        room_code_label: "Otaq kodu",
        btn_link: "Link",
        btn_qr: "QR",
        players_in_lobby: "Lobbiyə qoşulanlar",
        status_waiting: "Gözlənilir",
        status_started: "Oyun davam edir",
        waiting_players: "Oyunçuların qoşulması gözlənilir...",
        role_config_title: "Rolların tənzimlənməsi",
        special_roles_label: "Xüsusi rollar:",
        villagers_label: "Dinc sakinlər:",
        btn_start_game: "Oyunu başlat",
        min_players_needed: "Ən azı 3 oyunçu lazımdır",
        btn_end_game: "Oyunu bitir və otağı bağla",
        confirm_end_game: "Oyunu bitirmək və otağı bağlamaq istədiyinizdən əminsiniz?",
        qr_title: "QR kodu oxudun",
        qr_subtitle: "Oyunçuların tez qoşulması üçün",
        btn_close: "Bağla",
        timer_start: "Başla",
        timer_pause: "Fasilə",
        timer_reset: "Sıfırla",
        timer_finished: "Oyunçunun çıxış vaxtı bitdi!",
        link_copied: "Dəvət linki kopyalandı!",
        roles_exceed_players: "Xüsusi rolların sayı oyunçuların sayından çox ola bilməz!",
        player_eliminated: "Oyunçu oyundan çıxarıldı",
        player_restored: "Oyunçu oyuna qaytarıldı",
        role_assigned_toast: "Sizə təyin edilmiş rol: ",
        player_eliminated_toast: "Siz aparıcı tərəfindən oyundan çıxarıldınız",
        player_restored_toast: "Aparıcı sizi oyuna qaytardı!",
        game_ended_toast: "Oyun aparıcı tərəfindən bitirildi",
        your_role: "Sizin Rolunuz",
        waiting_role_deal: "Rolların paylanması gözlənilir...",
        role_dealt_hint: "Rol paylandı! Açmaq üçün toxunun",
        tap_to_reveal: "Açmaq üçün toxunun",
        hide_role: "Rolu gizlət",
        peek_role: "Rola baxmaq",
        you_are_eliminated: "Siz bu oyundan çıxarıldınız",
        not_found_title: "XƏTA",
        not_found_msg: "Otaq və ya səhifə tapılmadı.",
        btn_to_home: "Ana səhifəyə",
        
        // Game Phases & Balance
        phase_title: "Oyun Fazası",
        phase_day: "Gündüz (Müzakirə)",
        phase_voting: "Səsvermə",
        phase_night: "Gecə (Şəhər yatır)",
        phase_day_short: "Gündüz",
        phase_voting_short: "Səsvermə",
        phase_night_short: "Gecə",
        day_num_label: "Gündüz",
        night_overlay_title: "Gecə düşdü...",
        night_overlay_subtitle: "Bütün şəhər yatır. Gözlərinizi yumun və aparıcını dinləyin.",
        voting_overlay_title: "Səsvermə vaxtı!",
        voting_overlay_subtitle: "Kimin şəhərdən çıxarılacağına səs verin.",
        
        // Live Voting System
        voting_box_title: "Canlı Səsvermə",
        select_candidates_hint: "Səsverməyə çıxarılan oyunçuları seçin:",
        select_all_btn: "Hamısını seç",
        btn_open_voting: "Səsverməni başlat (30 san)",
        btn_close_voting: "Səsverməni dayandır",
        voting_in_progress: "Səsvermə gedir...",
        voting_time_up: "Səsvermə vaxtı bitdi!",
        vote_received_toast: "Səsiniz qeydə alındı!",
        abstain_vote: "Heç kimə (Bitərəf)",
        voted_out_title: "Səsvermənin nəticəsi:",
        voted_out_desc: "ən çox səs toplayaraq oyundan çıxarılır!",
        voting_tie: "Bərabərlik! Heç kim çıxarılmadı.",
        btn_confirm_elim: "Çıxarılmanı təsdiq et",
        btn_pardon: "Bağışla (Oyunda saxla)",
        btn_skip_voting: "Keç (Heç kim çıxarılmadı)",
        btn_revote: "Yenidən səsvermə",
        cannot_vote_self: "Özünüzə səs verə bilməzsiniz!",
        pardon_toast: "Oyunçu bağışlandı və oyunda qaldı!",
        skip_voting_toast: "Səsvermə keçildi — heç kim çıxarılmadı.",
        
        // Ghost / Spectator Mode
        ghost_mode_title: "👁️ Müşahidəçi Rejimi (Bütün Rollar)",
        ghost_mode_desc: "Siz oyundan çıxarılmısınız, lakin bütün oyunçuların rollarını canlı görə bilərsiniz:",
        status_alive_badge: "Sağdır",
        status_dead_badge: "Çıxarılıb",
        
        balance_title: "Canlı Qüvvələr Balansı",
        balance_mafia: "Mafiya:",
        balance_town: "Dinc sakin:",
        balance_total: "Sağ qalan:",
        
        winner_mafia_title: "🔴 MAFİYA QALİB GƏLDİ!",
        winner_mafia_desc: "Mafiya şəhəri tamamilə ələ keçirdi.",
        winner_town_title: "🟢 DİNC ŞƏHƏR QALİB GƏLDİ!",
        winner_town_desc: "Bütün cinayətkarlar ifşa edildi və aradan qaldırıldı.",
        winner_maniac_title: "🟣 MANYAQ QALİB GƏLDİ!",
        winner_maniac_desc: "Tək qatil hər kəsi aradan qaldıraraq sağ qaldı.",
        
        // End Game Results Screen
        game_results_title: "Oyunun Nəticələri",
        game_over_title: "OYUN BAŞA ÇATDI",
        your_team_won: "Təbriklər! Komandanız qalib gəldi! 🎉",
        your_team_lost: "Təəssüf ki, komandanız məğlub oldu.",
        player_roster_title: "Bütün Oyunçuların Rolları",
        btn_back_home: "Əsas menyuya qayıt",
        stat_alive_town: "Sağ qalan şəhər:",
        stat_alive_mafia: "Sağ qalan mafiya:",
        stat_alive_neutral: "Sağ qalan tək qatil:",
        stat_game_duration: "Oyun müddəti:",
        time_minutes_short: "dəq",
        time_seconds_short: "san",
        
        // Custom Roles Builder
        add_custom_role_btn: "Öz rolunu yarat",
        custom_role_modal_title: "Yeni Rol Yarat",
        role_name_label: "Rolun adı",
        role_name_placeholder: "Məs: Casus, Mühafizəçi, Vəkil...",
        role_team_label: "Tərəf / Komanda",
        role_icon_label: "İkonka seçin",
        role_color_label: "Rəng seçin",
        role_desc_label: "Qabiliyyət və Təsvir",
        role_desc_placeholder: "Bu rolun gecə və ya gündüz hansı qabiliyyəti var...",
        btn_create_role: "Rolu əlavə et",
        btn_cancel: "İmtina",
        role_created_toast: "Yeni rol uğurla əlavə edildi!",
        role_deleted_toast: "Rol silindi.",
        ability_label: "Qabiliyyət",
        
        // Roles
        role_mafia: "Mafiya",
        role_don: "Don",
        role_doctor: "Həkim",
        role_sheriff: "Komissar",
        role_maniac: "Manyak",
        role_kamikaze: "Kamikadze",
        role_villager: "Dinc Sakin",
        
        team_mafia: "Mafiya",
        team_don: "Mafiya Başçısı",
        team_town: "Dinc Şəhər",
        team_neutral: "Tək Qatil",
        
        desc_mafia: "<strong>Hədəf:</strong> Dinc sakinləri aradan qaldırmaq və şəhəri ələ keçirmək.<br><strong>Fəaliyyət:</strong> Gecə mafiya ilə birlikdə oyanır və qurban seçir.",
        desc_don: "<strong>Hədəf:</strong> Mafiyaya rəhbərlik etmək və Komissarı tapmaq.<br><strong>Fəaliyyət:</strong> Gecə Komissarı axtarır. Bərabər səsvermədə son söz Donundur.",
        desc_doctor: "<strong>Hədəf:</strong> Dinc sakinləri xilas etmək.<br><strong>Fəaliyyət:</strong> Hər gecə bir oyunçunu sağaldır. Özünü ard-arda 2 gecə sağalda bilməz.",
        desc_sheriff: "<strong>Hədəf:</strong> Mafiyanı tapmaq və ifşa etmək.<br><strong>Fəaliyyət:</strong> Hər gecə bir oyunçunu yoxlayaraq mafiya olub-olmadığını öyrənir.",
        desc_maniac: "<strong>Hədəf:</strong> Təkbaşına sağ qalmaq.<br><strong>Fəaliyyət:</strong> Özü üçün oynayır, hər gecə mafiyadan asılı olmayaraq bir qurban seçir.",
        desc_kamikaze: "<strong>Hədəf:</strong> Özünü qurban verərək şəhərə kömək etmək.<br><strong>Fəaliyyət:</strong> Səsvermədə çıxarılarsa, istədiyi bir oyunçunu özü ilə aparır.",
        desc_villager: "<strong>Hədəf:</strong> Mafiyanı aşkar edib səsvermədə çıxarmaq.<br><strong>Fəaliyyət:</strong> Gecə yatır, gündüz müzakirələrdə və səsvermədə iştirak edir."
    },
    ru: {
        app_title: "Мафия онлайн",
        brand_title_1: "MAFIA",
        brand_title_2: "GAME",
        brand_subtitle: "Город засыпает... Просыпается мафия",
        tab_join: "Войти в игру",
        tab_host: "Ведущий",
        label_nickname: "Ваше имя / никнейм",
        placeholder_nickname: "Например: Дон Корлеоне",
        label_room_code: "Код комнаты",
        placeholder_room_code: "5-значный код (напр. 49201)",
        btn_join: "Присоединиться",
        host_desc: "Создайте игровую комнату, чтобы быть ведущим, настраивать баланс ролей и управлять игровым процессом в реальном времени.",
        btn_create_room: "Создать новую комнату",
        room_code_label: "Код комнаты",
        btn_link: "Ссылка",
        btn_qr: "QR",
        players_in_lobby: "Игроки в лобби",
        status_waiting: "Ожидание",
        status_started: "Игра идет",
        waiting_players: "Ожидание подключения игроков...",
        role_config_title: "Настройка ролей",
        special_roles_label: "Особых:",
        villagers_label: "Мирные жители:",
        btn_start_game: "Начать игру",
        min_players_needed: "Нужно минимум 3 игрока",
        btn_end_game: "Завершить и закрыть комнату",
        confirm_end_game: "Вы уверены, что хотите завершить игру и закрыть комнату?",
        qr_title: "Сканируйте QR",
        qr_subtitle: "Для быстрого подключения игроков",
        btn_close: "Закрыть",
        timer_start: "Старт",
        timer_pause: "Пауза",
        timer_reset: "Сброс",
        timer_finished: "Время речи игрока истекло!",
        link_copied: "Ссылка скопирована в буфер обмена!",
        roles_exceed_players: "Количество особых ролей не может превышать число игроков!",
        player_eliminated: "Игрок выбыл",
        player_restored: "Игрок возвращен в игру",
        role_assigned_toast: "Вам назначена роль: ",
        player_eliminated_toast: "Вы были исключены из игры ведущим",
        player_restored_toast: "Ведущий вернул вас в игру!",
        game_ended_toast: "Игра завершена ведущим",
        your_role: "Ваша Роль",
        waiting_role_deal: "Ожидание раздачи ролей...",
        role_dealt_hint: "Роль выдана! Нажмите, чтобы открыть",
        tap_to_reveal: "Нажмите, чтобы открыть",
        hide_role: "Скрыть роль",
        peek_role: "Подглядеть роль",
        you_are_eliminated: "Вы выбыли из этой партии",
        not_found_title: "ОШИБКА",
        not_found_msg: "Вы зашли не в тот переулок... Комната или страница не найдена.",
        btn_to_home: "На главную",
        
        // Game Phases & Balance
        phase_title: "Фаза игры",
        phase_day: "День (Обсуждение)",
        phase_voting: "Голосование",
        phase_night: "Ночь (Город засыпает)",
        phase_day_short: "День",
        phase_voting_short: "Голосование",
        phase_night_short: "Ночь",
        day_num_label: "День",
        night_overlay_title: "Город засыпает...",
        night_overlay_subtitle: "Наступила ночь. Закройте глаза и слушайте указания ведущего.",
        voting_overlay_title: "Время голосования!",
        voting_overlay_subtitle: "Город решает, кто покинет игру.",
        
        // Live Voting System
        voting_box_title: "Живое Голосование",
        select_candidates_hint: "Выберите кандидатов на голосование:",
        select_all_btn: "Выбрать всех",
        btn_open_voting: "Открыть голосование (30 сек)",
        btn_close_voting: "Завершить голосование",
        voting_in_progress: "Идет сбор голосов...",
        voting_time_up: "Время голосования истекло!",
        vote_received_toast: "Ваш голос принят!",
        abstain_vote: "Ни против кого (Воздержаться)",
        voted_out_title: "Итог голосования:",
        voted_out_desc: "набирает большинство голосов и покидает игру!",
        voting_tie: "Ничья! Никто не исключен.",
        btn_confirm_elim: "Подтвердить исключение",
        btn_pardon: "Помиловать (Оставить в игре)",
        btn_skip_voting: "Пропустить (Никто не выбыл)",
        btn_revote: "Переголосовать",
        cannot_vote_self: "Нельзя голосовать против самого себя!",
        pardon_toast: "Игрок помилован и остался в игре!",
        skip_voting_toast: "Голосование пропущено — никто не выбыл.",
        
        // Ghost / Spectator Mode
        ghost_mode_title: "👁️ Режим Наблюдателя (Все Роли)",
        ghost_mode_desc: "Вы выбыли из игры, но можете наблюдать за всеми скрытыми ролями:",
        status_alive_badge: "Жив",
        status_dead_badge: "Выбыл",
        
        balance_title: "Баланс живых сил",
        balance_mafia: "Мафия:",
        balance_town: "Мирные:",
        balance_total: "Живых:",
        
        winner_mafia_title: "🔴 ПОБЕДА МАФИИ!",
        winner_mafia_desc: "Мафия получила численное превосходство и захватила город.",
        winner_town_title: "🟢 ПОБЕДА ГОРОДА!",
        winner_town_desc: "Все преступники были найдены и обезврежены.",
        winner_maniac_title: "🟣 ПОБЕДА МАНЬЯКА!",
        winner_maniac_desc: "Одинокий маньяк устранил всех и остался последним выжившим.",
        
        // End Game Results Screen
        game_results_title: "Итоги Игры",
        game_over_title: "ИГРА ЗАВЕРШЕНА",
        your_team_won: "Поздравляем! Ваша команда победила! 🎉",
        your_team_lost: "К сожалению, ваша команда проиграла.",
        player_roster_title: "Раскрытие всех ролей",
        btn_back_home: "В главное меню",
        stat_alive_town: "Выжившие мирные:",
        stat_alive_mafia: "Выжившая мафия:",
        stat_alive_neutral: "Выжившие маньяки:",
        stat_game_duration: "Время игры:",
        time_minutes_short: "мин",
        time_seconds_short: "сек",
        
        // Custom Roles Builder
        add_custom_role_btn: "Создать свою роль",
        custom_role_modal_title: "Конструктор роли",
        role_name_label: "Название роли",
        role_name_placeholder: "Напр: Шпион, Телохранитель, Адвокат...",
        role_team_label: "Команда / Сторона",
        role_icon_label: "Выберите иконку",
        role_color_label: "Выберите цвет",
        role_desc_label: "Способность и описание",
        role_desc_placeholder: "Что делает эта роль днем или ночью...",
        btn_create_role: "Добавить роль",
        btn_cancel: "Отмена",
        role_created_toast: "Новая роль успешно создана!",
        role_deleted_toast: "Роль удалена.",
        ability_label: "Способность",
        
        // Roles
        role_mafia: "Мафия",
        role_don: "Дон",
        role_doctor: "Доктор",
        role_sheriff: "Шериф",
        role_maniac: "Маньяк",
        role_kamikaze: "Камикадзе",
        role_villager: "Мирный житель",
        
        team_mafia: "Мафия",
        team_don: "Глава Мафии",
        team_town: "Мирный город",
        team_neutral: "Одиночка",
        
        desc_mafia: "<strong>Цель:</strong> Устранить мирных жителей и захватить город.<br><strong>Действие:</strong> Просыпаетесь ночью вместе с мафией и выбираете жертву.",
        desc_don: "<strong>Цель:</strong> Руководить мафией и уничтожить город.<br><strong>Действие:</strong> Ночью ищет Шерифа. При равных голосах решающее слово за Доном.",
        desc_doctor: "<strong>Цель:</strong> Спасать мирных жителей.<br><strong>Действие:</strong> Ночью выбирает одного игрока для исцеления. Нельзя лечить себя 2 ночи подряд.",
        desc_sheriff: "<strong>Цель:</strong> Найти и нейтрализовать мафию.<br><strong>Действие:</strong> Ночью проверяет одного игрока, чтобы узнать, мафия он или нет.",
        desc_maniac: "<strong>Цель:</strong> Остаться последним выжившим.<br><strong>Действие:</strong> Играет сам за себя. Каждую ночь выбирает жертву независимо от мафии.",
        desc_kamikaze: "<strong>Цель:</strong> Пожертвовать собой ради победы города.<br><strong>Действие:</strong> Если вас казнят на голосовании, вы забираете любого игрока с собой.",
        desc_villager: "<strong>Цель:</strong> Вычислить мафию и проголосовать за изгнание.<br><strong>Действие:</strong> Ночью спит. Днем участвует в обсуждениях и голосованиях."
    },
    en: {
        app_title: "Mafia Online",
        brand_title_1: "MAFIA",
        brand_title_2: "GAME",
        brand_subtitle: "City falls asleep... Mafia wakes up",
        tab_join: "Join Game",
        tab_host: "Host",
        label_nickname: "Your Name / Nickname",
        placeholder_nickname: "e.g., Don Corleone",
        label_room_code: "Room Code",
        placeholder_room_code: "5-digit code (e.g. 49201)",
        btn_join: "Join Game",
        host_desc: "Create a game room to host, balance roles, and manage live gameplay in real-time.",
        btn_create_room: "Create New Room",
        room_code_label: "Room Code",
        btn_link: "Link",
        btn_qr: "QR",
        players_in_lobby: "Players in Lobby",
        status_waiting: "Waiting",
        status_started: "Game in Progress",
        waiting_players: "Waiting for players to join...",
        role_config_title: "Configure Roles",
        special_roles_label: "Special Roles:",
        villagers_label: "Villagers:",
        btn_start_game: "Start Game",
        min_players_needed: "Need at least 3 players",
        btn_end_game: "End Game and Close Room",
        confirm_end_game: "Are you sure you want to end the game and close the room?",
        qr_title: "Scan QR Code",
        qr_subtitle: "For quick player connection",
        btn_close: "Close",
        timer_start: "Start",
        timer_pause: "Pause",
        timer_reset: "Reset",
        timer_finished: "Player speech time expired!",
        link_copied: "Invite link copied to clipboard!",
        roles_exceed_players: "Special roles cannot exceed player count!",
        player_eliminated: "Player eliminated",
        player_restored: "Player restored",
        role_assigned_toast: "You have been assigned: ",
        player_eliminated_toast: "You have been eliminated by the host",
        player_restored_toast: "Host restored you back into the game!",
        game_ended_toast: "Game ended by host",
        your_role: "Your Role",
        waiting_role_deal: "Waiting for role assignment...",
        role_dealt_hint: "Roles dealt! Tap to reveal",
        tap_to_reveal: "Tap to reveal",
        hide_role: "Hide Role",
        peek_role: "Peek at role",
        you_are_eliminated: "You have been eliminated from this game",
        not_found_title: "ERROR",
        not_found_msg: "You wandered into the wrong alley... Room not found.",
        btn_to_home: "Home",
        
        // Game Phases & Balance
        phase_title: "Game Phase",
        phase_day: "Day (Discussion)",
        phase_voting: "Voting",
        phase_night: "Night (City sleeps)",
        phase_day_short: "Day",
        phase_voting_short: "Voting",
        phase_night_short: "Night",
        day_num_label: "Day",
        night_overlay_title: "Night falls...",
        night_overlay_subtitle: "The entire city is asleep. Close your eyes and follow host instructions.",
        voting_overlay_title: "Voting Phase!",
        voting_overlay_subtitle: "The city decides who will be eliminated.",
        
        // Live Voting System
        voting_box_title: "Live Voting",
        select_candidates_hint: "Select nominated candidates:",
        select_all_btn: "Select All",
        btn_open_voting: "Start Voting (30s)",
        btn_close_voting: "End Voting",
        voting_in_progress: "Collecting votes...",
        voting_time_up: "Voting time is up!",
        vote_received_toast: "Your vote has been cast!",
        abstain_vote: "Abstain (None)",
        voted_out_title: "Voting Result:",
        voted_out_desc: "received the most votes and is eliminated!",
        voting_tie: "Tie! No player was eliminated.",
        btn_confirm_elim: "Confirm Elimination",
        btn_pardon: "Pardon (Keep in game)",
        btn_skip_voting: "Skip (No one eliminated)",
        btn_revote: "Revote",
        cannot_vote_self: "You cannot vote for yourself!",
        pardon_toast: "Player pardoned and remains in the game!",
        skip_voting_toast: "Voting skipped — no one was eliminated.",
        
        // Ghost / Spectator Mode
        ghost_mode_title: "👁️ Spectator Mode (All Roles)",
        ghost_mode_desc: "You have been eliminated, but you can now spectate all players' roles:",
        status_alive_badge: "Alive",
        status_dead_badge: "Dead",
        
        balance_title: "Live Force Balance",
        balance_mafia: "Mafia:",
        balance_town: "Town:",
        balance_total: "Alive:",
        
        winner_mafia_title: "🔴 MAFIA WON!",
        winner_mafia_desc: "Mafia gained majority and seized control of the city.",
        winner_town_title: "🟢 TOWN WON!",
        winner_town_desc: "All criminals were investigated and eliminated.",
        winner_maniac_title: "🟣 MANIAC WON!",
        winner_maniac_desc: "The solo maniac outlasted everyone and won.",
        
        // End Game Results Screen
        game_results_title: "Game Results",
        game_over_title: "GAME OVER",
        your_team_won: "Congratulations! Your team won! 🎉",
        your_team_lost: "Unfortunately, your team lost.",
        player_roster_title: "All Players & Roles Revealed",
        btn_back_home: "Back to Home",
        stat_alive_town: "Surviving Town:",
        stat_alive_mafia: "Surviving Mafia:",
        stat_alive_neutral: "Surviving Solo:",
        stat_game_duration: "Match Duration:",
        time_minutes_short: "min",
        time_seconds_short: "sec",
        
        // Custom Roles Builder
        add_custom_role_btn: "Create Custom Role",
        custom_role_modal_title: "Create Custom Role",
        role_name_label: "Role Name",
        role_name_placeholder: "E.g. Spy, Bodyguard, Lawyer...",
        role_team_label: "Team / Alignment",
        role_icon_label: "Choose Icon",
        role_color_label: "Choose Color",
        role_desc_label: "Ability & Description",
        role_desc_placeholder: "What this role does at night or day...",
        btn_create_role: "Add Role",
        btn_cancel: "Cancel",
        role_created_toast: "New role created successfully!",
        role_deleted_toast: "Role deleted.",
        ability_label: "Ability",
        
        // Roles
        role_mafia: "Mafia",
        role_don: "Don",
        role_doctor: "Doctor",
        role_sheriff: "Sheriff",
        role_maniac: "Maniac",
        role_kamikaze: "Kamikaze",
        role_villager: "Villager",
        
        team_mafia: "Mafia",
        team_don: "Mafia Leader",
        team_town: "Town",
        team_neutral: "Solo",
        
        desc_mafia: "<strong>Goal:</strong> Eliminate all town members.<br><strong>Action:</strong> Wakes up at night with the mafia to pick a victim.",
        desc_don: "<strong>Goal:</strong> Lead the mafia and find the Sheriff.<br><strong>Action:</strong> Checks for the Sheriff each night. Has deciding vote on ties.",
        desc_doctor: "<strong>Goal:</strong> Protect town members.<br><strong>Action:</strong> Heals one player each night. Cannot heal self twice in a row.",
        desc_sheriff: "<strong>Goal:</strong> Discover and eliminate the mafia.<br><strong>Action:</strong> Investigates one player each night to learn if they are mafia.",
        desc_maniac: "<strong>Goal:</strong> Be the last person standing.<br><strong>Action:</strong> Plays solo, strikes independently of mafia each night.",
        desc_kamikaze: "<strong>Goal:</strong> Sacrifice yourself for the town.<br><strong>Action:</strong> If eliminated at town vote, drags any chosen player along.",
        desc_villager: "<strong>Goal:</strong> Find and vote out the mafia.<br><strong>Action:</strong> Sleeps at night, debates and votes during the day."
    }
};

let currentLang = localStorage.getItem('mafia_lang') || 'az';

function t(key) {
    const langDict = TRANSLATIONS[currentLang] || TRANSLATIONS.az;
    return langDict[key] || TRANSLATIONS.ru[key] || key;
}

function setLanguage(lang) {
    if (!TRANSLATIONS[lang]) return;
    currentLang = lang;
    localStorage.setItem('mafia_lang', lang);
    applyTranslations();
    
    document.querySelectorAll('.lang-btn').forEach(btn => {
        if (btn.dataset.lang === lang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

function applyTranslations() {
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.az;
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.innerHTML = dict[key];
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (dict[key]) {
            el.placeholder = dict[key];
        }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (dict[key]) {
            el.title = dict[key];
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
});
