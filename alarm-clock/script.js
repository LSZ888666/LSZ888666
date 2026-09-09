/**
 * 闹钟应用 (Alarm Clock Application)
 *
 * 功能：
 * - 实时显示当前时间
 * - 设置多个闹钟
 * - 闹钟到时提醒（声音 + 弹窗）
 * - 删除已设置的闹钟
 */

(function () {
  "use strict";

  // --- DOM Elements ---
  var clockEl = document.getElementById("clock");
  var alarmTimeInput = document.getElementById("alarm-time");
  var setAlarmBtn = document.getElementById("set-alarm-btn");
  var alarmListEl = document.getElementById("alarm-list");
  var noAlarmMsg = document.getElementById("no-alarm-msg");
  var alarmAlert = document.getElementById("alarm-alert");
  var alarmAlertTime = document.getElementById("alarm-alert-time");
  var dismissBtn = document.getElementById("dismiss-btn");

  // --- State ---
  var alarms = []; // Array of { id, time (24-hour zero-padded "HH:MM:SS"), triggered }
  var nextId = 1;
  var audioCtx = null;
  var alarmOscillator = null;

  // --- Helpers ---

  /**
   * Pad a number to two digits.
   */
  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  /**
   * Get current time as HH:MM:SS string.
   */
  function currentTimeString() {
    var now = new Date();
    return pad(now.getHours()) + ":" + pad(now.getMinutes()) + ":" + pad(now.getSeconds());
  }

  /**
   * Normalize a time input value to HH:MM:SS.
   * The <input type="time"> may return HH:MM without seconds.
   */
  function normalizeTime(value) {
    if (!value) return "";
    var parts = value.split(":");
    if (parts.length === 2) {
      parts.push("00");
    }
    return parts.map(function (p) { return pad(parseInt(p, 10)); }).join(":");
  }

  // --- Audio ---

  /**
   * Start playing an alarm sound using Web Audio API.
   */
  function startAlarmSound() {
    if (alarmOscillator) return; // already playing
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      alarmOscillator = audioCtx.createOscillator();
      var gainNode = audioCtx.createGain();
      alarmOscillator.type = "square";
      alarmOscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
      gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);
      alarmOscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      alarmOscillator.start();
    } catch (_) {
      // Web Audio API not available – ignore silently
    }
  }

  /**
   * Stop the alarm sound.
   */
  function stopAlarmSound() {
    if (alarmOscillator) {
      try {
        alarmOscillator.stop();
      } catch (_) { /* ignore */ }
      alarmOscillator = null;
    }
  }

  // --- Rendering ---

  /**
   * Re-render the alarm list UI.
   */
  function renderAlarms() {
    alarmListEl.innerHTML = "";
    if (alarms.length === 0) {
      noAlarmMsg.style.display = "block";
      return;
    }
    noAlarmMsg.style.display = "none";

    alarms.forEach(function (alarm) {
      var li = document.createElement("li");

      var span = document.createElement("span");
      span.className = "alarm-time-label";
      span.textContent = alarm.time;
      li.appendChild(span);

      var status = document.createElement("span");
      status.className = "alarm-status" + (alarm.triggered ? " triggered" : "");
      status.textContent = alarm.triggered ? "已响铃" : "等待中";
      li.appendChild(status);

      var delBtn = document.createElement("button");
      delBtn.textContent = "删除";
      delBtn.setAttribute("data-id", alarm.id);
      delBtn.addEventListener("click", function () {
        removeAlarm(alarm.id);
      });
      li.appendChild(delBtn);

      alarmListEl.appendChild(li);
    });
  }

  // --- Alarm Management ---

  /**
   * Add a new alarm.
   */
  function addAlarm(timeStr) {
    alarms.push({ id: nextId++, time: timeStr, triggered: false });
    renderAlarms();
  }

  /**
   * Remove an alarm by id.
   */
  function removeAlarm(id) {
    alarms = alarms.filter(function (a) { return a.id !== id; });
    renderAlarms();
  }

  /**
   * Check alarms against the current time and trigger if matched.
   */
  function checkAlarms(nowStr) {
    alarms.forEach(function (alarm) {
      if (!alarm.triggered && alarm.time === nowStr) {
        alarm.triggered = true;
        triggerAlarm(alarm);
      }
    });
  }

  /**
   * Show the alarm alert overlay and play sound.
   */
  function triggerAlarm(alarm) {
    alarmAlertTime.textContent = "闹钟时间：" + alarm.time;
    alarmAlert.classList.remove("hidden");
    startAlarmSound();
    renderAlarms();
  }

  /**
   * Dismiss the alarm alert.
   */
  function dismissAlarm() {
    alarmAlert.classList.add("hidden");
    stopAlarmSound();
  }

  // --- Event Handlers ---

  setAlarmBtn.addEventListener("click", function () {
    var raw = alarmTimeInput.value;
    if (!raw) {
      alert("请先选择一个时间！");
      return;
    }
    var timeStr = normalizeTime(raw);
    addAlarm(timeStr);
    alarmTimeInput.value = "";
  });

  dismissBtn.addEventListener("click", dismissAlarm);

  // --- Main Loop ---

  function tick() {
    var nowStr = currentTimeString();
    clockEl.textContent = nowStr;
    checkAlarms(nowStr);
  }

  // Update clock every 500ms for frequent updates
  tick();
  setInterval(tick, 500);
})();
