function loadData() {
    //document.getElementById("description").innerHTML = "New text!";
    
    var packagename = window.location.search.replace("?package=", "").split("&")[0];
    
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var jsondata = JSON.parse(this.responseText);
            document.getElementById("description").innerHTML = jsondata.description;
            document.getElementById("author").innerHTML = jsondata.author;
            document.getElementById("bugreporturl").innerHTML = jsondata.bugreporturl;
            document.getElementById("website").innerHTML = jsondata.website;
            document.getElementById("tos").innerHTML = jsondata.tos;
            document.getElementById("category").innerHTML = jsondata.category;
            document.getElementById("image1").src = jsondata.image1;
            document.getElementById("image2").src = jsondata.image2;
            document.getElementById("image3").src = jsondata.image3;
        }
    };
    xmlhttp.open("GET", "https://feren-os.github.io/store-data/curated/apt/"+packagename+".json", true);
    xmlhttp.send();
}
