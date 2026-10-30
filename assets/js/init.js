
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

htmx.onLoad((e) => {
    items = document.getElementsByClassName("rotate")
    for (i=0; i<items.length; i++) {
        items[i].setAttribute("style", "transform:rotate(" + (Math.random() * 360) + "deg)")
    }

    Fancybox.bind("[data-fancybox]", {
    // Your custom options
    });
})

htmx.on("messages", (e) => {
    e.detail.value.forEach(createToast)
})
