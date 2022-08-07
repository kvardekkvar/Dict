var activeSource
var editModalState

window.addEventListener('pywebviewready', function() {
  var container = document.getElementById('pywebview-status')
  //container.innerHTML = '<i>pywebview</i> is ready'

  window.editModalState = new EditModal();
  getSources()

})

/*window.onerror = function(msg, url, linenumber) {
    alert('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
    return true;
}*/

function showResponse(response) {
  var container = document.getElementById('response-container')
  container.innerText = response.message
  container.style.display = 'none'
  return response
}

function setOnclicksSources(payload) {
  var sources = document.getElementsByClassName('source')
  for (var i = 0; i < sources.length; i++) {
    var source = sources[i];
    //source.onclick = onLeftClickSource
    source.addEventListener("click", e => onLeftClickSource(e.target))
    source.addEventListener("contextmenu", e => onRightClick(e, e.target))
  }

  return payload
}

function setOnclicksWords(payload) {
  var sources = document.getElementsByClassName('word')
  for (var i = 0; i < sources.length; i++) {
    var source = sources[i];
    //source.onclick = onLeftClickSource
    source.addEventListener("contextmenu", e => onRightClick(e, e.target))
    source.setAttribute('tabindex', '0')
    source.addEventListener('keydown', function(e) {
      if (e.shiftKey && e.keyCode == '38') {
        moveWordOneUp(e.target.getAttribute('data-id'))
      }
    });

  }

  return payload
}


function onLeftClickSource(elem) {
  activeSource?.classList.toggle("active-source")
  elem.classList.toggle("active-source")
  window.activeSource = elem

  getWords(activeSource.getAttribute("data-id"))
  //resetWords(activeSource)
}

function onRightClick(e, elem) {
  e.preventDefault();
  var rect = elem.getBoundingClientRect();
  console.log(rect.top, rect.right, rect.bottom, rect.left);
  var modal = document.getElementById('edit-modal')
  modal.classList.toggle('hidden');
  modal.style.position = "absolute";
  modal.style.left = rect.left + 'px';
  modal.style.top = rect.top + 'px';

  document.getElementById('modal-inp').style.width = elem.offsetWidth + 'px';
  elem.classList.contains('source') ? modal.classList.add('modal-for-source') : modal.classList.remove('modal-for-source');

  document.getElementById('modal-inp').value = elem.innerHTML;
  window.editModalState.elem = elem
  window.editModalState.type = elem.classList.contains('source') ? 'source' : 'word'
  document.getElementById('modal-root').classList.add('visible');
  return false;
}


class EditModal {
  elem;
  type;
  modal;
  input;
  buttonEdit;
  buttonNothing;
  buttonDelete;


  constructor() {
    this.modal = document.getElementById('edit-modal');
    this.input = document.getElementById('modal-inp');
    this.buttonEdit = document.getElementById('edit-btn');
    this.buttonEdit.addEventListener('click', this.edit.bind(this));
    this.buttonNothing = document.getElementById('nothing-btn');
    this.buttonNothing.addEventListener('click', this.doNothing.bind(this));
    this.buttonDelete = document.getElementById('delete-btn');
    this.buttonDelete.addEventListener('click', this.delete.bind(this));

    document.getElementById('modal-root').addEventListener('click', this.clickOutside.bind(this));
    this.modal.addEventListener('click', this.clickInside.bind(this));
  }

  doNothing() {
    this.close();
  }

  edit() {
    if (this.type == 'source') {
      var newtext = this.input.value;
      var changedsource = this.elem.getAttribute("data-id");
      this.close()
      return pywebview.api.editSource(newtext, changedsource, 'None', 's').then(showResponse).then(getSources)
    } else if (this.type == 'word') {
      var newtext = this.input.value;
      var changedWordId = this.elem.getAttribute("data-id");
      var activeSource = window.activeSource.getAttribute("data-id");
      this.close()
      return pywebview.api.editWord(newtext, changedWordId, activeSource).then(showResponse).then(getWords)

    } else {
      alert('error with type of elem for modal')
    }

  }
  delete() {
    if (this.type == 'source') {
      var deletedSourceId = this.elem.getAttribute("data-id");
      this.close()
      return pywebview.api.deleteSource(deletedSourceId).then(showResponse).then(getSources)
    } else if (this.type == 'word') {
      var deletedWordId = this.elem.getAttribute("data-id");
      var activeSource = window.activeSource.getAttribute("data-id");
      this.close()
      return pywebview.api.deleteWord(deletedWordId, activeSource).then(showResponse).then(getWords)

    } else {
      alert('error')
    }
  }
  close() {
    document.getElementById('modal-root').classList.remove('visible');
    this.modal.classList.toggle('hidden')
  }
  clickOutside() {
    this.close();
  }
  clickInside(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    return false;
  }

}






function getWords() {
  activeSourceId = window.activeSource?.getAttribute('data-id')
  return pywebview.api.getWords(activeSourceId).then(showResponse).then(resetWords).then(setOnclicksWords)

}

function drawWord(word) {
  word = JSON.parse(word)
  var containerSources = document.getElementById('w')
  newElem = document.createElement('div')
  newElem.innerHTML = word.text
  newElem.className = 'word'
  newElem.setAttribute("data-id", word.id)
  containerSources.appendChild(newElem)
}

function resetWords(response) {
  var list = response.content
  var containerSources = document.getElementById('w')
  containerSources.innerHTML = ''
  list.forEach(drawWord)
  return response
}

function addWord() {
  newWord = document.getElementById("inp-w").value.trim();
  document.getElementById("inp-w").value = '';
  return pywebview.api.addWord(newWord, window.activeSource?.getAttribute("data-id") ?? "").then(getWords)
    .then(p => {
      objDiv = document.getElementById('w');
      objDiv.scrollTop = objDiv.scrollHeight;
      return p;
    })

}






function getSources() {
  return pywebview.api.getSources().then(showResponse).then(resetSources).then(setOnclicksSources)
}


function drawSource(source) {
  source = JSON.parse(source)
  var containerSources = document.getElementById('s')
  newElem = document.createElement('div')
  newElem.innerHTML = source.text
  newElem.className = 'source'
  newElem.setAttribute("data-id", source.id)
  containerSources.appendChild(newElem)

  if (source.id == window.activeSource?.getAttribute("data-id")) {
    newElem.classList.toggle('active-source')
    window.activeSource = newElem
  }

}

function resetSources(response) {
  var list = response.content
  var containerSources = document.getElementById('s')
  containerSources.innerHTML = ''
  list.forEach(drawSource)
  return response
}

function addSource() {
  newSource = document.getElementById("inp-s").value.trim();
  document.getElementById("inp-s").value = '';
  return pywebview.api.addSource(newSource).then(getSources)
    .then(p => {
      objDiv = document.getElementById('w');
      objDiv.scrollTop = objDiv.scrollHeight;
      return p;
    })

}




function moveWordOneUp(wordId) {
  sourceId = window.activeSource?.getAttribute('data-id')
  return pywebview.api.moveWordOneUp(wordId, sourceId).then(showResponse).then(getWords)
}




function syncXml() {
  return pywebview.api.syncXml().then(showResponse);
}