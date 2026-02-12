import cv2

VIDEO_PATH = "2048246-hd_1920_1080_24fps.mp4"  # 필요하면 파일명만 바꿔줘

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise RuntimeError("비디오를 못 열었어요. 파일 경로/코덱 문제일 수 있어요.")

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"width={w}, height={h}, fps={fps}")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1080p가 버벅이면 “표시용으로만” 1280폭으로 축소
    if w > 1280:
        new_w = 1280
        new_h = int(h * (new_w / w))
        frame_show = cv2.resize(frame, (new_w, new_h))
    else:
        frame_show = frame

    cv2.imshow("video", frame_show)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    if key == ord("s"):
        cv2.imwrite("frame.jpg", frame)
        print("saved frame.jpg")

cap.release()
cv2.destroyAllWindows()
