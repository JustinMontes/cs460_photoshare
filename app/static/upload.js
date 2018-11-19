window.onload = function(){
  var modal = document.getElementById('modal-container');
  var btn = document.getElementById("post-button");
  var exit_btn = document.getElementsByClassName("close_btn")[0];
  var like_btn = document.getElementById('like');

  var num = 0;

  like_btn.onclick = function() {
    

  }

  btn.onclick = function() {
    modal.style.display = 'block';

  }



  exit_btn.onclick = function() {
      modal.style.display = "none";
  }

  window.onclick = function(event) {
      if (event.target == modal) {
          modal.style.display = "none";
      }
  }
}
