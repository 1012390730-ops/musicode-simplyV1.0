from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import librosa
import base64
import tempfile
import os

class SimpleMusicProcessor:
    def detect_tempo(self, audio_data, sr):
        """简化的节奏检测"""
        try:
            # 使用更简单的节奏检测方法
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=sr, hop_length=512)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            return float(tempo)
        except Exception as e:
            print(f"Tempo detection error: {e}")
            return 120.0
    
    def detect_key(self, audio_data, sr):
        """简化的调性检测"""
        try:
            # 使用更稳定的 chroma 特征提取
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sr)
            chroma_avg = np.mean(chroma, axis=1)
            
            major_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_index = np.argmax(chroma_avg)
            
            return major_keys[key_index]
        except Exception as e:
            print(f"Key detection error: {e}")
            return 'C'
    
    def generate_chords(self, key, tempo):
        """生成基础和弦"""
        chord_progressions = {
            'C': ['C', 'G', 'Am', 'F'],
            'G': ['G', 'D', 'Em', 'C'], 
            'D': ['D', 'A', 'Bm', 'G'],
            'A': ['A', 'E', 'F#m', 'D'],
            'E': ['E', 'B', 'C#m', 'A'],
            'F': ['F', 'C', 'Dm', 'Bb'],
            'Am': ['Am', 'G', 'C', 'F']
        }
        return chord_progressions.get(key, ['C', 'G', 'Am', 'F'])

def handler(req, context):
    """Vercel Serverless Function 处理函数"""
    try:
        if req.method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            }
        
        elif req.method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'AI Music API is running!',
                    'endpoints': {
                        'POST /api/process-music': 'Process audio and generate music'
                    }
                })
            }
        
        elif req.method == 'POST':
            # 解析请求体
            body = req.body
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body
            
            audio_b64 = data.get('audioData', '')
            
            if not audio_b64:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'No audio data provided'
                    })
                }
            
            # 解码音频
            try:
                audio_bytes = base64.b64decode(audio_b64)
            except:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Invalid audio data format'
                    })
                }
            
            # 使用临时文件处理音频
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            try:
                # 加载音频文件，限制时长和采样率以减少内存使用
                audio_data, sr = librosa.load(tmp_path, sr=22050, duration=20)
                
                processor = SimpleMusicProcessor()
                tempo = processor.detect_tempo(audio_data, sr)
                key = processor.detect_key(audio_data, sr)
                chords = processor.generate_chords(key, tempo)
                
                response = {
                    'success': True,
                    'tempo': tempo,
                    'key': key,
                    'chords': chords,
                    'message': '音乐处理成功！'
                }
                
            except Exception as audio_error:
                response = {
                    'success': False,
                    'error': f'Audio processing error: {str(audio_error)}'
                }
            
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(response)
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Method not allowed'
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
        }

# 为了兼容性，保留旧的 handler 类
class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
