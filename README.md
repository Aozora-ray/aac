# aac
## 構成
### データ
- setting.json
    - 
- user_information.json
    - is_login
    - REVEL_SESSION
    - csrf_token
- contest/
    - contest_information.json
        - url
        - task/
            - url
            - status
### 関数
- check_initialization
```
if カレントディレクトリにsetting.jsonがない
    error_handling(0)
if カレントディレクトリにuser_information.jsonがない
    error_handling(0)
```
- error_handling(int error_code)
```
if error_code == 0
    初期化が必要です。
exit(1)
```
- get_login_information
- 
### コマンド
- initialize
- login
```
get_login_information()
```
- logout
- make
- remove
- download
- test
- submit

# sample
```
=-=-= Test Result =-=-=-=-=-=-=-=
Test Time : 2026-02-18 20:10:00
Task      : A
Code Size : 1611 Byte
Test Case :
| 1.txt |  AC  | 1ms | 3284 KiB |
| 2.txt |  WA  | 2ms | 4224 KiB |
----- input -----------
3
----- output ----------
10
----- your output -----
343
-----------------------
| 3.txt |  AC  | 4ms | 3941 KiB |
Status    : WA
Exec Time :
Memory    :
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
=-=-= Submission -=-=-=-=-=-=-=-=
Submission Time :
Task            :
Score           :
Code Size       :
Status          :
Exec Time       :
Memory          :
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
```