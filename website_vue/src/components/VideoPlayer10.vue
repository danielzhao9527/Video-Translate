<template>
  <div class="video-container">
    <input
      type="text"
      v-model="videoUrlInput"
      placeholder="请输入视频链接"
      class="url-input"
    />
    <button @click="loadVideo" class="load-button">加载视频</button>

    <div v-if="videoSrc">
      <video
        id="video-player"
        class="video-js vjs-default-skin"
        controls
        preload="auto"
        width="100%"
        height="auto"
        ref="video"
      ></video>

      <!-- 外部语言选择下拉框 -->
      <div v-if="videoLoaded" class="external-language-select">
        <label for="language">选择翻译语言:</label>
        <el-select
          v-model="selectedLanguage"
          id="language"
          @change="onExternalLanguageChange"
          placeholder="请选择语言"
        >
          <el-option label="英语" value="en"></el-option>
          <el-option label="中文" value="zh"></el-option>
          <el-option label="法语" value="fr"></el-option>
          <el-option label="日语" value="ja"></el-option>
          <el-option label="韩语" value="ko"></el-option>
          <el-option label="西班牙语" value="es"></el-option>
        </el-select>
      </div>
    </div>
  </div>
</template>


<script>
import axios from 'axios';
import videojs from 'video.js';

export default {
  data() {
    return {
      videoUrlInput: '',
      videoSrc: '',
      audioPath: '',
      selectedLanguage: '', // 当前选中语言
      player: null,
      videoLoaded: false, // 标志视频是否加载
    };
  },
  methods: {
    loadVideo() {
      axios
        .post(
          '/api/get_video_info/',
          { video_url: this.videoUrlInput, cookies: this.getCookies() },
          { withCredentials: true }
        )
        .then((response) => {
          if (response.data.video_url) {
            // 重置播放器及相关数据
            this.videoSrc = '';
            this.selectedLanguage = '';
            if (this.player) {
              this.player.dispose();
              this.player = null;
              this.videoLoaded = false;
            }

            this.$nextTick(() => {
              this.videoSrc = response.data.video_url;
              this.audioPath = `http://localhost:8000/${response.data.audio_path}`;
              this.sourceSubtitlePath = response.data.subtitle_path;
              this.$nextTick(() => this.initPlayer());
            });
          } else {
            alert('加载视频失败: 没有返回视频链接');
          }
        })
        .catch((error) => {
          alert(
            '加载视频时出错: ' + (error.response?.data?.error || error.message)
          );
        });
    },

    onExternalLanguageChange() {
      if (!this.selectedLanguage) {
        alert('请先选择语言');
        return;
      }
      const textTracks = this.player.textTracks();
      let trackFound = false;

      Array.from(textTracks).forEach((track) => {
        if (track.language === this.selectedLanguage) {
          track.mode = 'showing'; // 显示对应字幕
           trackFound = true;
        } else {
          track.mode = 'disabled'; // 隐藏其他字幕
        }
      });

      if (trackFound) {
        // 手动触发 texttrackchange 事件
        this.player.trigger('texttrackchange');
      } else {
        console.warn(`没有找到对应语言的轨道: ${this.selectedLanguage}`);
      }

      this.loadSubtitles();
    },

    // loadSubtitles() {
    //   if (!this.selectedLanguage) {
    //     console.warn('语言未选择或无效，无法加载字幕');
    //     return;
    //   }
    //   console.log(`1当前选择的语言: ${this.selectedLanguage}`);  // 增加日志
    //   const currentLanguage = this.selectedLanguage; // 暂存语言
    //   axios
    //     .post(
    //       '/api/generate_subtitles/',
    //       { audio_path: this.audioPath, language: currentLanguage, subtitle_path: this.sourceSubtitlePath  },
    //       { withCredentials: true }
    //     )
    //     .then((response) => {
    //       const vttFileUrl = `http://localhost:8000/${response.data.translated_subtitles}`;
    //       console.log('字幕文件生成成功，路径:', vttFileUrl);
    //
    //       console.log(`2当前选择的语言: ${this.selectedLanguage}`);  // 增加日志
    //
    //       const player = videojs.getPlayer('video-player');
    //
    //       // 遍历现有的字幕轨道，删除匹配语言的轨道
    //       const textTracks = Array.from(player.remoteTextTracks());
    //       textTracks.forEach((track) => {
    //         if (track.language === currentLanguage) {
    //           console.log(`移除旧字幕轨道: ${track.language}`);
    //           player.removeRemoteTextTrack(track);
    //         }
    //       });
    //
    //       console.log(`3当前选择的语言: ${this.selectedLanguage}`);  // 增加日志
    //
    //
    //       // 添加新的字幕轨道
    //       console.log(`添加新的字幕轨道: ${currentLanguage}`);
    //       const newTrack = player.addRemoteTextTrack(
    //         {
    //           kind: 'subtitles',
    //           src: vttFileUrl,
    //           srclang: currentLanguage,
    //           label: this.getLanguageLabel(currentLanguage),
    //         },
    //         false
    //       ).track;
    //
    //       // 确保新的轨道启用
    //       newTrack.mode = 'showing';
    //
    //       // // 禁用其他轨道
    //       // textTracks.forEach((track) => {
    //       //   if (track.language !== this.selectedLanguage) {
    //       //     track.mode = 'disabled';
    //       //   }
    //       // });
    //
    //       // 打印调试信息
    //       console.log(`新轨道添加完成: ${newTrack.label} (${newTrack.language})`);
    //
    //       // 更新内部状态
    //       this.selectedLanguage = currentLanguage;
    //
    //       // 同步外部下拉框
    //       this.syncLanguageDropdown();
    //
    //
    //     })
    //     .catch((error) => {
    //       console.error('生成字幕时出错:', error.response?.data?.error || error.message);
    //       alert('生成字幕时出错: ' + (error.response?.data?.error || error.message));
    //     });
    // },

    loadSubtitles() {
      if (!this.selectedLanguage) {
        console.warn('语言未选择或无效，无法加载字幕');
        return;
      }

      console.log(`当前选择的语言: ${this.selectedLanguage}`);
      const currentLanguage = this.selectedLanguage; // 暂存语言

      const player = videojs.getPlayer('video-player');

      // 遍历现有的字幕轨道，检查是否已存在匹配语言的轨道
      const textTracks = Array.from(player.remoteTextTracks());
      for (const track of textTracks) {
        if (track.language === currentLanguage) {
          console.log(`找到匹配的字幕轨道: ${track.language}`);

          // 如果轨道的 src 已经是所需的字幕文件，直接启用
          if (track.src) {
            console.log(`字幕轨道已存在并启用，无需重新请求`);
            track.mode = 'showing';
            // 更新内部状态
            this.selectedLanguage = currentLanguage;

            // 同步外部下拉框
            this.syncLanguageDropdown();
            return;
          }
        }
      }

      // 如果未找到合适的字幕轨道，向后端请求生成字幕
      axios
        .post(
          '/api/generate_subtitles/',
          {
            audio_path: this.audioPath,
            language: currentLanguage,
            subtitle_path: this.sourceSubtitlePath,
          },
          { withCredentials: true }
        )
        .then((response) => {
          const vttFileUrl = `http://localhost:8000/${response.data.translated_subtitles}`;
          console.log('字幕文件生成成功，路径:', vttFileUrl);

          //遍历现有的字幕轨道，删除匹配语言的轨道
          const textTracks = Array.from(player.remoteTextTracks());
          textTracks.forEach((track) => {
            if (track.language === currentLanguage) {
              console.log(`移除旧字幕轨道: ${track.language}`);
              player.removeRemoteTextTrack(track);
            }
          });

          // 添加新的字幕轨道
          console.log(`添加新的字幕轨道: ${currentLanguage}`);
          const newTrack = player.addRemoteTextTrack(
            {
              kind: 'subtitles',
              src: vttFileUrl,
              srclang: currentLanguage,
              label: this.getLanguageLabel(currentLanguage),
            },
            false
          ).track;

          // 确保新的轨道启用
          newTrack.mode = 'showing';


          // 打印调试信息
          console.log(`新轨道添加完成: ${newTrack.label} (${newTrack.language})`);

          // 更新内部状态
          this.selectedLanguage = currentLanguage;

          // 同步外部下拉框
          this.syncLanguageDropdown();
        })
        .catch((error) => {
          console.error('生成字幕时出错:', error.response?.data?.error || error.message);
          alert('生成字幕时出错: ' + (error.response?.data?.error || error.message));
        });
    },




    getLanguageLabel(language) {
      const languageMap = {
        en: '英语',
        zh: '中文',
        fr: '法语',
        ja: '日语',
        ko: '韩语',
        es: '西班牙语',
      };
      return languageMap[language] || `未知语言 (${language})`;
    },



        initPlayer() {
          this.player = videojs(this.$refs.video, {
            controls: true,
            autoplay: false,
            preload: 'auto',
            sources: [{ src: this.videoSrc, type: 'video/mp4' }],
            textTrackSettings: true,
          });

          this.player.ready(() => {
            this.videoLoaded = true;

            // 延迟添加字幕轨道，确保播放器已完全初始化
            this.$nextTick(() => {
              const languages = [
                { label: '英语', value: 'en' },
                { label: '中文', value: 'zh' },
                { label: '法语', value: 'fr' },
                { label: '日语', value: 'ja' },
                { label: '韩语', value: 'ko' },
                { label: '西班牙语', value: 'es' },
              ];

              languages.forEach((lang) => {
                console.log(`Adding text track for: ${lang.label} with srclang: ${lang.value}`);
                videojs.getPlayer('video-player').addRemoteTextTrack(
                  {
                    kind: 'subtitles',
                    src: '',  // 初始为空
                    srclang: lang.value,  // 确保这里设置正确的语言代码
                    label: lang.label,  // 显示语言名称
                    default: false,
                  },
                  false
                );
              });

              // 同步 Captions 按钮逻辑
              this.syncCaptionsButton();
            });
          });
        },


        syncLanguageDropdown() {
          const languageSelect = document.getElementById('language');
          if (languageSelect) {
            languageSelect.value = this.selectedLanguage;
          }
          },



        syncCaptionsButton() {
          const textTracks = this.player.textTracks();

          this.player.on('texttrackchange', () => {
            const activeTrack = Array.from(textTracks).find((track) => track.mode === 'showing');

            if (activeTrack) {
              console.log(`当前激活字幕轨道: ${activeTrack.label} (${activeTrack.language})`);
              if (activeTrack.language !== this.selectedLanguage) {
                this.selectedLanguage = activeTrack.language; // 同步选中语言
                this.loadSubtitles(); // 触发后端请求
              }
            } else {
              console.log('当前无激活字幕轨道');
              this.selectedLanguage = ''; // 如果没有启用字幕，设置为空
            }

            // 同步外部下拉框
            this.syncLanguageDropdown();
          });
        },



    getCookies() {
      return document.cookie;
    },
  },
  beforeUnmount() {
    if (this.player) {
      this.player.dispose();
    }
  },
};
</script>


<style scoped>
.video-container {
  width: 100%;
  margin: 0 auto;
}

.url-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 20px;
}

.load-button {
  padding: 10px 20px;
  margin: 10px;
}

.video-js {
  width: 100%;
  height: 800px;
  position: relative;
}

.external-language-select {
  margin-top: 20px;
}
</style>


