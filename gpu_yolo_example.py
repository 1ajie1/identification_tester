"""
GPU加速YOLO检测示例
使用配置好的环境进行GPU加速的YOLO目标检测
"""

import torch
import cv2
import numpy as np
from ultralytics import YOLO
import time

def check_gpu_status():
    """检查GPU状态"""
    print("=== GPU状态检查 ===")
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"GPU设备数: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"GPU {i} 内存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
    
    print(f"NumPy版本: {np.__version__}")
    print(f"OpenCV版本: {cv2.__version__}")

def create_yolo_model(model_name='yolo11n.pt'):
    """创建YOLO模型并配置GPU"""
    print(f"\n=== 加载YOLO模型: {model_name} ===")
    
    try:
        # 加载模型
        model = YOLO(model_name)
        print("✓ YOLO模型加载成功")
        
        # 设置设备
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        print(f"✓ 模型设备: {device}")
        
        return model, device
    
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        return None, None

def benchmark_inference(model, device, image_size=(640, 640), num_runs=10):
    """基准测试推理性能"""
    if model is None:
        print("模型未加载，跳过基准测试")
        return
    
    print(f"\n=== 推理性能测试 ({device}) ===")
    
    # 创建测试图像
    test_image = np.random.randint(0, 255, (*image_size, 3), dtype=np.uint8)
    
    # 预热GPU
    print("预热GPU...")
    for _ in range(3):
        _ = model(test_image, verbose=False)
    
    # 性能测试
    times = []
    print(f"开始{num_runs}次推理测试...")
    
    for i in range(num_runs):
        start_time = time.time()
        results = model(test_image, verbose=False)
        end_time = time.time()
        inference_time = end_time - start_time
        times.append(inference_time)
        print(f"推理 {i+1:2d}: {inference_time:.4f}s")
    
    # 统计结果
    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)
    fps = 1.0 / avg_time
    
    print(f"\n性能统计:")
    print(f"平均推理时间: {avg_time:.4f}s")
    print(f"最快推理时间: {min_time:.4f}s")
    print(f"最慢推理时间: {max_time:.4f}s")
    print(f"平均FPS: {fps:.2f}")

def detect_objects_in_image(model, image_path, save_path=None):
    """在图像中检测目标"""
    if model is None:
        print("模型未加载，跳过目标检测")
        return
    
    print(f"\n=== 图像目标检测: {image_path} ===")
    
    try:
        # 检查图像是否存在
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法读取图像: {image_path}")
            return
        
        print(f"图像尺寸: {image.shape}")
        
        # 进行检测
        start_time = time.time()
        results = model(image_path)
        inference_time = time.time() - start_time
        
        print(f"推理时间: {inference_time:.4f}s")
        
        # 处理结果
        for r in results:
            boxes = r.boxes
            if boxes is not None and len(boxes) > 0:
                print(f"检测到 {len(boxes)} 个目标:")
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = model.names[cls]
                    print(f"  {i+1}. {class_name}: {conf:.3f}")
                
                # 保存标注图像
                if save_path:
                    annotated_frame = r.plot()
                    cv2.imwrite(save_path, annotated_frame)
                    print(f"标注图像已保存: {save_path}")
            else:
                print("未检测到任何目标")
    
    except Exception as e:
        print(f"检测过程出错: {e}")

def main():
    """主函数"""
    print("GPU加速YOLO检测示例")
    print("=" * 50)
    
    # 检查GPU状态
    check_gpu_status()
    
    # 创建模型
    model, device = create_yolo_model()
    
    if model is None:
        print("模型创建失败，退出")
        return
    
    # 性能基准测试
    benchmark_inference(model, device)
    
    # 检测示例图像
    test_images = ['tmp/bus.jpg', 'tmp/test.jpg']
    
    for img_path in test_images:
        try:
            if cv2.imread(img_path) is not None:
                output_path = f"tmp/output_{img_path.split('/')[-1]}"
                detect_objects_in_image(model, img_path, output_path)
                break
        except:
            continue
    else:
        print("\n未找到测试图像，创建随机图像进行演示...")
        # 创建随机测试图像
        random_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        test_path = 'tmp/random_test.jpg'
        cv2.imwrite(test_path, random_image)
        detect_objects_in_image(model, test_path, 'tmp/output_random.jpg')
    
    print("\n" + "=" * 50)
    print("示例完成！")
    
    if torch.cuda.is_available():
        print("🚀 GPU加速已启用，享受快速的YOLO检测！")
    else:
        print("⚠ 使用CPU模式，考虑安装CUDA以获得更好性能")

if __name__ == "__main__":
    main()
