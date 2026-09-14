
    window.onerror = function(msg, url, line) {
      alert("產生器網頁錯誤：" + msg + "\n在：" + url + " 第 " + line + " 行");
      return false;
    };
  