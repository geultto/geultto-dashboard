# 글또 운영 대시보드 레포

## VSCode, Docker를 이용해 열기
- Visual Studio Code, Docker 설치가 필요합니다.
1. Repository를 클론 받아주세요.
2. VSCode를 실행해 Extensions 중 Dev Containers를 설치합니다.
3. Cmd(Control) + Shift + p -> `Dev Containers: Open Folder in Container...` 를 선택합니다.
4. 클론받은 폴더를 선택해주세요
5. `From 'dockerfile'` 를 선택합니다.
6. additioanl features는 선택하지 않고 넘어갑니다.
7. 컨테이너가 만들어지면 `streamlit run dashboard.py` 명령어를 입력합니다.

## notice 
- .streamlt/secrets.toml 파일은 레포에 업로드 하지 않았습니다. 기여가 필요하거나 오프라인 환경에서의 테스트가 필요하실 경우 따로 요청 부탁드립니다!
- 추후 적당한 배포 방법을 찾으면 [geultto](https://github.com/geultto)로 옮겨볼 예정