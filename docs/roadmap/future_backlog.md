# Future Development Roadmap

## English

### Overview

This document provides technical guidelines for the next stages of high-level project expansion and commercialization.

---

### 1. Multi-Camera Orchestration

Scaling beyond the current 1:1 pipeline to efficiently manage dozens of cameras.

#### Technical Design: Process Manager

- **Multiprocessing Parallelization**: Bypass Python's GIL by assigning independent processes per camera.
- **Master-Worker Structure**:
  - **Master**: Monitors worker health (Heartbeat) and handles auto-restarts for failed processes.
  - **Worker (Pipeline)**: Executes inference and event processing for individual cameras.
- **Shared Resource Management**: Transition to an "Inference Server" architecture where multiple processes request inference from a single model instance to prevent GPU VRAM exhaustion.

---

### 2. Self-learning Pipeline (Active Learning)

A continuous loop to improve model accuracy using field data.

#### Active Learning Loop

- **Confidence-based Sampling**: Automatically extract frames with ambiguous predictions (confidence 0.3~0.5).
- **Labeling Assistance**: Extracted frames are added to training datasets after manager approval/correction.
- **Retraining & Deployment**: Perform automatic fine-tuning when enough data is collected and deploy new weights (`.pt`) after validation.

---

### 3. Advanced Vision Capabilities

Expanding beyond simple detection into complex behavioral analysis.

#### High-level Tracking & ReID

- **DeepSORT/ByteTrack Enhancement**: Combat occlusion and preserve object IDs across frames even when objects exit and re-enter.
- **Behavioral Analysis (Pose Estimation)**: Identify static and dynamic postures such as 'falling', 'collapsing', or 'fighting'.

---

### 4. Performance Optimization

Maximizing efficiency within limited hardware resources.

#### Backend Acceleration

- **TensorRT / OpenVINO**: Convert PyTorch models to specialized acceleration formats to increase inference speed by 2~5x.
- **Batch Processing**: Group multiple frames for simultaneous inference to maximize throughput for non-real-time processing.

---

### 5. Deployment & Observability

- **Kubernetes Integration**: Deploy and horizontally scale pipelines as containerized units.
- **Centralized Logging**: Integrate with ELK Stack (Logstash, Elasticsearch, Kibana) to visualize event trends across all cameras.

### 6. Multi-Sensor Integration (Multimodal AI)

Enhancing safety awareness by combining visual data with complementary environmental sensors.

#### Technical Design: Composite Input

- **Multimodal Data Fusion**: Extend `FrameSource` to a generalized `DataSource` that aggregates synchronized video frames and sensor readings (e.g., ultrasonic, temperature, gas, sound).
- **Rule-based Decision Fusion**: Update `EventBuilder` to evaluate complex safety rules (e.g., [Person Detected (CCTV)] AND [Distance < 1m (Ultrasonic)] -> WARNING).
- **IoT Device Integration**: Implement adapters for standard protocols like MQTT or Modbus to communicate with hardware PLC and sensor hubs.

---

## 한국어

### 개요

본 문서는 AI 파이프라인 프로젝트의 다음 단계인 고도화 및 상용화 수준의 확장을 위한 기술적 가이드라인을 제공합니다.

---

### 1. Multi-Camera Orchestration (다중 카메라 오케스트레이션)

현재의 1:1 파이프라인 구조를 뛰어넘어, 수십 대 이상의 카메라를 효율적으로 관리하기 위한 설계입니다.

#### 기술 설계: 프로세스 매니저 (Process Manager)

- **Multiprocessing 기반 병렬화**: 파이썬의 GIL(Global Interpreter Lock)을 피해 카메라당 독립적인 프로세스를 할당합니다.
- **Master-Worker 구조**:
  - **Master**: 각 카메라 프로세스의 상태(Heartbeat)를 감시하고, 비정상 종료 시 자동 재시작(Auto-restart)을 담당합니다.
  - **Worker (Pipeline)**: 개별 카메라의 추론 및 이벤트를 처리합니다.
- **Shared Resource Management**: GPU 메모리 부족을 방지하기 위해 여러 프로세스가 하나의 모델 인스턴스에 추론을 요청하는 '추론 서버(Inference Server)' 구조로의 단계적 전환을 목표로 합니다.

---

### 2. Self-learning Pipeline (자율 학습 및 능동 학습)

현장에서 발생하는 데이터를 활용하여 모델의 정확도를 지속적으로 향상시키는 루프를 구축합니다.

#### Active Learning Loop

- **Confidence-based Sampling**: AI가 판단하기 모호한(신뢰도 0.3~0.5 사이) 프레임을 자동으로 추출하여 별도의 서버에 전송합니다.
- **자동 라벨링 보조**: 추출된 프레임에 대해 현장 관리자가 승인/수정만 하면 자동으로 학습 데이터셋에 추가됩니다.
- **재학습 및 배포**: 데이터가 일정량 모이면 자동으로 파인튜닝(Fine-tuning)을 수행하고, 성능 검증 후 새로운 가중치(`.pt`)를 파이프라인에 배포합니다.

---

### 3. Advanced Vision Capabilities (고급 시각 분석)

단순 탐지를 넘어선 복합적인 분석 기능을 추가합니다.

#### High-level Tracking & ReID

- **DeepSORT/ByteTrack 고도화**: 객체가 가려지거나 화면 밖으로 나갔다 들어와도 동일 인물로 인식하는 Re-Identification 능력을 강화합니다.
- **행동 분석 (Pose Estimation)**: 단순히 구역 진입이 아닌 '넘어짐', '쓰러짐', '격투' 등 특정 정적/동적 자세를 식별하는 모델을 연동합니다.

---

### 4. Performance Optimization (성능 가속)

제한된 하드웨어 리소스에서 최대의 효율을 뽑아내기 위한 최적화입니다.

#### Backend Acceleration

- **TensorRT / OpenVINO**: 일반 파이토치 모델을 전용 가속 포맷으로 변환하여 추론 속도를 2~5배 향상시키고 전력 소모를 줄입니다.
- **Batch Processing**: 실시간 스트림이 아닌 대량의 영상을 처리할 때 여러 장의 프레임을 한 번에 추론하여 처리량을 극대화합니다.

---

### 5. Deployment & Observability (운영 및 관측성)

- **Kubernetes 연동**: 수백 대의 카메라를 컨테이너 단위로 배포하고 수평 확장(Scaling)합니다.
- **중앙 집중형 로깅**: ELK Stack(Elasticsearch, Logstash, Kibana)과 연동하여 모든 카메라의 이벤트 발생 추이를 시각화합니다.

---

### 6. Multi-Sensor Integration (멀티 센서 및 멀티모달 AI)

시각 데이터와 환경 센서를 결합하여 객체 탐지의 정확도를 높이고 상황 인지 능력을 극대화합니다.

#### 기술 설계: 복합 데이터 퓨전 (Multimodal Data Fusion)

- **통합 데이터 소스**: `FrameSource`를 `DataSource`로 확장하여 비디오 프레임뿐만 아니라 초음파, 온도, 가스, 소리 등 다양한 센서 값을 동기화된 형태로 수집합니다.
- **복합 룰 엔진 (Rule Fusion)**: "CCTV로 확인된 사람"과 "초음파 센서로 측정된 거리 데이터"를 조합하여 더욱 정교한 사고 예방 로직을 구축합니다.
- **표준 프로토콜 지원**: MQTT, Modbus 등 산업용 표준 프로토콜 어댑터를 구현하여 하드웨어 PLC 및 센서 허브와의 통신을 지원합니다.

---

### 관련 문서 링크

- [Implementation Docs Index](../implementation/README.md)
- [Ops Runbook](../legacy/ops/ops_runbook.md)
- [Project Artifacts](../../README.md)
