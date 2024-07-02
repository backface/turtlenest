function createToast(message) {
    const element = document.createElement('div');
    element.className +=  message.tags + " "
    const span = document.createElement('span');
    span.innerText = message.message
    element.appendChild(span)
    htmx.find(".toast").appendChild(element)
    element.addEventListener("click", function(e) {
        element.remove()
    }, false);
    setTimeout(() => {
        element.remove()
    }, 5000);
}
  

htmx.on("messages", (e) => {
    console.log(e.detail.value)
    e.detail.value.forEach(createToast)
})
