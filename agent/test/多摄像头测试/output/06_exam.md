# 做题式测试 — 召回/精确/IoU 评估

**Started**: 2026-05-12T02:48:58.976106  
**Elapsed**: 14.36s  

## Results

| Suite | Total | Passed | Failed |
|-------|------:|-------:|-------:|
| cross_camera 摄像头召回/精确/IoU | 25 | 25 | 0 |
| negative 多摄意图检测 | 8 | 8 | 0 |
| cross_camera 汇总统计 | 1 | 1 | 0 |
| **Total** | **34** | **34** | **0** |

## cross_camera 摄像头召回/精确/IoU

- ✅ **[PASS] Did a person with beige jacket appear in camera G329 and then appear a**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G329'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G329']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G329']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark long coat appear in camera G329 and then appear**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G329'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G329']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G329']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark jacket (hood up) appear in camera G329 and then**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G329'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G329']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G329']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark jacket (hood up) appear in camera G328 and then**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G339'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G339']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G339']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark jacket (hood up) appear in camera G329 and then**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G329', 'G339'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G329', 'G339']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G329', 'G339']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with black coat with fur-trimmed hood appear in camera G3**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G329'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G329']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G329']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with black coat with fur-trimmed hood appear in camera G3**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G339'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G339']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G339']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with black coat with fur-trimmed hood appear in camera G3**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G329', 'G339'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G329', 'G339']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G329', 'G339']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with white shirt appear in camera G328 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G339'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G339']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G339']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with white shirt appear in camera G328 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G328', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G328', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G328', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with white shirt appear in camera G424 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G339 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G421'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G421']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G421']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G424 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G339 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G506'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G506']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G506']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G424 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G421', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G421', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G421', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G506 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G421', 'G506'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G421', 'G506']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G421', 'G506']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey hoodie appear in camera G424 and then app**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G424', 'G506'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G424', 'G506']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G424', 'G506']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with long dark coat appear in camera G424 and then appear**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark jacket appear in camera G424 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with beige/khaki coat appear in camera G424 and then appe**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with brown jacket with dark hood/scarf appear in camera G**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with light grey coat with black hat appear in camera G424**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G424'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G424']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G424']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with black hoodie (hood up) appear in camera G421 and the**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G421'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G421']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G421']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark jacket appear in camera G421 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G421'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G421']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G421']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286
- ✅ **[PASS] Did a person with dark hoodie appear in camera G421 and then appear ag**
  mc=True recall=1.00 prec=0.29 IoU=0.29 | expected=['G339', 'G421'] found=['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `expected_cameras`: ['G339', 'G421']
  - `found_cameras`: ['G328', 'G329', 'G339', 'G421', 'G424', 'G506', 'G508']
  - `intersection`: ['G339', 'G421']
  - `recall`: 1.000
  - `precision`: 0.286
  - `iou`: 0.286

## negative 多摄意图检测

- ✅ **Did a person with dark hoodie from camera G421 also appear in camera G508?**
  multi_camera=True (expected=True)
- ✅ **Did a person with dark long coat from camera G329 also appear in camera G424?**
  multi_camera=True (expected=True)
- ✅ **Did a person with beige jacket from camera G329 also appear in camera G424?**
  multi_camera=True (expected=True)
- ✅ **Did a person with black coat with fur-trimmed hood from camera G329 also appear **
  multi_camera=True (expected=True)
- ✅ **Did a person with dark long coat from camera G329 also appear in camera G508?**
  multi_camera=True (expected=True)
- ✅ **Did a person with dark jacket (hood up) from camera G329 also appear in camera G**
  multi_camera=True (expected=True)
- ✅ **Did a person with brown jacket with dark hood/scarf from camera G424 also appear**
  multi_camera=True (expected=True)
- ✅ **Did a person with dark long coat from camera G328 also appear in camera G421?**
  multi_camera=True (expected=True)

## cross_camera 汇总统计

- ✅ **总体: 25/25 通过 (100.0%)**
  - `avg_recall`: 1.000
  - `avg_precision`: 0.286
  - `avg_iou`: 0.286
  - `passed`: 25
  - `total`: 25
