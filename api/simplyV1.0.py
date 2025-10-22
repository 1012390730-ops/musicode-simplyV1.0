from http.server import BaseHTTPRequestHandler
import json
import numpy as np
import librosa
import base64
import tempfile
import os


# 由于 Vercel 使用 Serverless Functions，我们需要使用不同的方式
class SimpleMusicProcessor:
    def detect_tempo(self, audio_data, sr):
        """简化的节奏检测"""
        try:
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            return float(tempo) if tempo else 120.0
        except:
            return 120.0

    def detect_key(self, audio_data, sr):
        """简化的调性检测"""
        try:
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=sr)
            chroma_avg = np.mean(chroma, axis=1)

            major_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_index = np.argmax(chroma_avg)

            return major_keys[key_index]
        except:
            return 'C'

    def generate_chords(self, key, tempo):
        """生成基础和弦"""
        chord_progressions = {
            'C': ['C', 'G', 'Am', 'F'],
            'G': ['G', 'D', 'Em', 'C'],
            'D': ['D', 'A', 'Bm', 'G'],
            'A': ['A', 'E', 'F#m', 'D'],
            'E': ['E', 'B', 'C#m', 'A'],
            'F': ['F', 'C', 'Dm', 'A#'],
            'Am': ['Am', 'G', 'C', 'F']
        }
        return chord_progressions.get(key, ['C', 'G', 'Am', 'F'])


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求 - 用于测试"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {
            'success': True,
            'message': 'AI Music API is running!',
            'endpoints': {
                'POST /api/process-music': 'Process audio and generate music'
            }
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        """处理 POST 请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            audio_b64 = data.get('audioData', '')

            if not audio_b64:
                raise ValueError("No audio data provided")

            # 解码音频
            audio_bytes = base64.b64decode(audio_b64)

            # 使用临时文件处理音频
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

            # 加载和处理音频
            try:
                audio_data, sr = librosa.load(tmp_path, sr=44100, duration=30)  # 限制30秒

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

            # 清理临时文件
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            response = {
                'success': False,
                'error': f'Request processing error: {str(e)}'
            }

        # 发送响应
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(response).encode('utf-8'))


# Vercel 需要这个
if __name__ == '__main__':
    from http.server import HTTPServer

    server = HTTPServer(('localhost', 8000), handler)
    server.serve_forever()