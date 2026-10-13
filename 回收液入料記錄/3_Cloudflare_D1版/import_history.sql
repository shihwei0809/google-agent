-- 匯入 Google Sheets 歷史資料至 Cloudflare D1 (egups-db)
INSERT OR REPLACE INTO recycle_records (
    id, date, license_plate, status, 
    t_before_url, v_photo_url, t_after_url, 
    before_time, after_time, duration,
    created_at, updated_at
) VALUES 
('1791764320575', '2026-10-12', 'HAB2810/C06', 'completed', 
 'https://drive.google.com/file/d/1knCerBbLCEapMdzfGrKyxi_s8U0KuNos/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1kzhpVdM9Jp8GYIpay_9dnMQao_ImSd8p/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1I18-4oEYfN1qOsIgUwLeuqXceKtYButr/view?usp=drivesdk', 
 '2026-10-12 08:18:54', '', NULL, '2026-10-12 08:18:54', '2026-10-12 08:18:54'),

('1791764485142', '2026-10-12', 'HAB2807/C07', 'completed', 
 'https://drive.google.com/file/d/1_VFYTdFgdtetkxpZ-wH210ezygsje3MK/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1rvJ5PXFCcL6MbCXqHaRM49PRS3IFdIz_/view?usp=drivesdk', 
 'https://drive.google.com/file/d/13A-IlATJYLHgIu0EuCrJjTQruM-t05SN/view?usp=drivesdk', 
 '2026-10-12 08:21:32', '', NULL, '2026-10-12 08:21:32', '2026-10-12 08:21:32'),

('1791764577574', '2026-10-12', '38Z7/TK643', 'completed', 
 'https://drive.google.com/file/d/1WV9SceCJ8rC3-BzVdNf5cwrfnIkbHfgl/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1jL0R5r20_8jgNlJBYAYX3n2LHEkIeetg/view?usp=drivesdk', 
 'https://drive.google.com/file/d/13GrIHzKUl9D4hiFVqf_lN7DsB3ziBdYl/view?usp=drivesdk', 
 '2026-10-12 08:23:06', '', NULL, '2026-10-12 08:23:06', '2026-10-12 08:23:06'),

('1791769218614', '2026-10-12', 'HAB6108/C05', 'completed', 
 'https://drive.google.com/file/d/1HV7GwQ1Mwxt0jZHDfNn8kEjgowNSWl1g/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1Jt32lVWB17x4MlLb8yzUInOfxY4zYSlI/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1_RD4Cp8AhbTSPPF6a93v2R_avCduZYG2/view?usp=drivesdk', 
 '2026-10-12 09:40:27', '2026-10-12 14:29:19', 289, '2026-10-12 09:40:27', '2026-10-12 14:29:19'),

('1791851538277', '2026-10-13', 'HAC-2597', 'completed', 
 'https://drive.google.com/file/d/10pu7cPhC4XJao2Q3_dicZ17p2ahZoCOU/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1yIsnPzHq6zv7wQC3aSU1nYrhe_QDKi1m/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1bJlC3kRBRjIrdsQSMryjHpJ98-rZ5vEm/view?usp=drivesdk', 
 '2026-10-13 08:32:18', '2026-10-13 08:34:03', 2, '2026-10-13 08:32:18', '2026-10-13 08:34:03'),

('1791852822481', '2026-10-13', 'HAC-2601', 'completed', 
 'https://drive.google.com/file/d/1v8MqY7qxEl83byoQ0e6Ie81oqSYusAce/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1QKZ_jCDHEJ133CHE9MuqijZAQOezwEwz/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1n58HGPgqJ6uGnqVWfVKfq2aRl6daVd8a/view?usp=drivesdk', 
 '2026-10-13 08:53:42', '2026-10-13 09:37:19', 44, '2026-10-13 08:53:42', '2026-10-13 09:37:19'),

('1791855181762', '2026-10-13', 'HAB-2810/C09', 'completed', 
 'https://drive.google.com/file/d/107kCEX2cFm18aUo6D7ftKIODTWVJzrEj/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1mKduhcFfVYCC20Wk2QUUrsZzJyVW4hEE/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1nEc3sxHsmyrEHrj_NpgMrt1rG36E7TZu/view?usp=drivesdk', 
 '2026-10-13 09:33:01', '2026-10-13 11:13:42', 101, '2026-10-13 09:33:01', '2026-10-13 11:13:42'),

('1791855530853', '2026-10-13', '38-Z7/tk643', 'completed', 
 'https://drive.google.com/file/d/1FVuQVtSUOn5GaknZhoaEPI3o05pTM3TP/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1E4uufV_ANqy2gMvssAc2iMT-Sm3u3JdQ/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1BofJTbVVXYftUecu7PDB0GoCEyZ2cyft/view?usp=drivesdk', 
 '2026-10-13 09:38:50', '2026-10-13 09:55:27', 17, '2026-10-13 09:38:50', '2026-10-13 09:55:27'),

('1791856385809', '2026-10-13', 'HAB-3977/659', 'completed', 
 'https://drive.google.com/file/d/1fO3lmuhC1QL7N2z8PpMSmKAnaGDiP0Cp/view?usp=drivesdk', 
 'https://drive.google.com/file/d/14u1OtcEp3HzSM2x8l-yqmuq10SL9aCgW/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1jKLpmIQ1xvXV9gMqQ7CyEIT6RfqO9-of/view?usp=drivesdk', 
 '2026-10-13 09:53:05', '2026-10-13 11:12:45', 80, '2026-10-13 09:53:05', '2026-10-13 11:12:45'),

('1791856493783', '2026-10-13', 'HAB-5991/CO8', 'completed', 
 'https://drive.google.com/file/d/1E9WQZOJiPopF9ADbNzGfn18jdsSmj5rm/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1MfNxx3GIqY7Mqmb3jZKHwiZe37TtKooI/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1q9sdzMdJYVuoMRh-eJCIqgpB5JQiXEyv/view?usp=drivesdk', 
 '2026-10-13 09:54:53', '2026-10-13 09:59:47', 5, '2026-10-13 09:54:53', '2026-10-13 09:59:47'),

('1791861890524', '2026-10-13', 'HAC-1100/659', 'completed', 
 'https://drive.google.com/file/d/1ijfDu381xJqsOw8XyUzBjzxPArnz8KOV/view?usp=drivesdk', 
 'https://drive.google.com/file/d/16wMsJYIZqQDaoUbM5_amh6w5xGiX0i9s/view?usp=drivesdk', 
 'https://drive.google.com/file/d/1rVJu8QxlQvQtHF6ZRmLNp0_Z2xViSwmz/view?usp=drivesdk', 
 '2026-10-13 11:24:50', '2026-10-13 13:25:59', 121, '2026-10-13 11:24:50', '2026-10-13 13:25:59');
