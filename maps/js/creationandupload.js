var tabfield;
var north_lat =[-20.00,29.05,-74.90,38.80,43.45,1.33,-31.0,-30.0]; //these arrays contains the latitudes and longitudes
var south_lat =[-20.16,28.05,-75.3,38.70,43.25,1.0,-31.5,-30.5];
var east_lon =[-67.45,23.89,123.90,33.40,8.0,-56.5,-137.0,80.5];
var west_lon =[-68.05,22.89,122.90,33.25,7.8,-57,-137.5,80.0];
var list_site=["Uyuni","Libya4","DomeC","TuzGolu","BOUSSOLE","Amazon","SPG","SIO"]; // this array contains the list of the instruments

function load(){
//this library is the one used to write into a file
// it uses flash player, you need to set it to make it work
//Add your local directory in the Trusted location settings
// change your settings here : http://www.macromedia.com/support/documentation/en/flashplayer/help/settings_manager04.html
					Downloadify.create('downloadify',{
					filename: function(){
						return document.getElementById("jsonfilename").value+".json";
					},
					data: function(){ 
						return jsoncreate(); 

					},
					onComplete: function(){ alert('Your file has been saved!'); },
					onCancel: function(){  alert('You have cancelled the saving of this file.'); },
					onError: function(){  alert('You must put something in the File Contents or there will be nothing to save!'); }, // to get this message you need the data returned to be ''
					swf: 'media/downloadify.swf',
					downloadImage: 'images/download.png',
					width: 100,
					height: 30,
					transparent: true,
					append: false
				});
			}
//this function create the json file
function jsoncreate ()  {

var json;
var instrum=document.getElementById('instrument').value;
var fileInput = document.querySelector('#name_file'); var reader = new FileReader();
if(document.getElementById("site").value=='Selection' || fileInput.files[0]==undefined || instrum=="Selection" || document.getElementById("jsonfilename").value==''){ //verify every field is filled
return ''; //to get the error message
}else 	for (var d=0;d<fileInput.files.length;d++){ //we can have more than one file
		var imagename= fileInput.files[d].name; //got the name of the file
		var imagetest=imagename.split('.');
		if (imagetest[(imagetest.length)-1]!='N1' && imagetest[(imagetest.length)-1]!='hdf' && imagetest[(imagetest.length)-1]!='zip'){ //zip put to test
 		return ''; //if not in the good format, return an error
		  }else   {  	
			json = "[";
			for (var k=0;k<fileInput.files.length;k++){
			json +="{\"filename\": \""+fileInput.files[k].name+"\",\"instrument\": \""+instrum+"\",\" region_name\": \""+document.getElementById("site").value+"\",\"region_coords\" : \""+coordscalcul(document.getElementById("site").value)+"\"}"
// json creation		
	if(k!=fileInput.files.length-1)	{
			json+=',';}
			}
			json+="]";
			return json;
			}
}}

function coordscalcul (value){ //create the part of the json which concerns the coords
var result='[';
switch(value){
case 'Uyuni':
result+=south_lat[0]+','+north_lat[0]+','+west_lon[0]+','+east_lon[0]+']';
break;
case 'Libya4':
result+=south_lat[1]+','+north_lat[1]+','+west_lon[1]+','+east_lon[1]+']';
break;
case 'DomeC':
result+=south_lat[2]+','+north_lat[2]+','+west_lon[2]+','+east_lon[2]+']';
break;
case 'TuzGolo':
result+=south_lat[3]+','+north_lat[3]+','+west_lon[3]+','+east_lon[3]+']';
break;
case 'BOUSSOLE':
result+=south_lat[4]+','+north_lat[4]+','+west_lon[4]+','+east_lon[4]+']';
break;
case 'Amazon':
result+=south_lat[5]+','+north_lat[5]+','+west_lon[5]+','+east_lon[5]+']';
break;
case 'SPG':
result+=south_lat[6]+','+north_lat[6]+','+west_lon[6]+','+east_lon[6]+']';
break;
case 'SIO':
result+=south_lat[7]+','+north_lat[7]+','+west_lon[7]+','+east_lon[7]+']';
break;

}return result;
}

$(document).ready(function(){ //filling the instrument select during the loading of the docs
	
    $.get('http://127.0.0.1:8000/api/v1/instrument?limit=0&filter_by=name',
        function(data){
            for(var i=0; i<data.objects.length; i++){
                $("#instrument").append($("<option>").val(data.objects[i].name).html(data.objects[i].name));
            } 
        }, 
        'jsonp' // /!\ NOT SURE IF SAFE         
    );
})



function submit() {
var fileInput = document.querySelector('#name_ingfile'); //get data from the file input
    	var reader = new FileReader();

if ( fileInput.files[0]== undefined){
		document.getElementById('message').innerHTML="Error: no json file found"; // if you click on the button while nothing is inside the file object
		document.getElementById('message').style.color="red";
		document.getElementById('message').style.visibility="visible";
}else {var jsonname= fileInput.files[0].name;
	var jsontest=jsonname.split('.');
		if (jsontest[(jsontest.length)-1]!='json' ){ 
		document.getElementById('message').innerHTML="Error: It's not a json file"; //check if the uploaded file is a json
		document.getElementById('message').style.color="red";
		document.getElementById('message').style.visibility="visible";
		}
		else{
		

   		 var xhr = new XMLHttpRequest();

   		 xhr.open('POST', '?????????????'); // dunno what to put there yet

  		 xhr.onload = function() {
 		       alert('Done!');
  		  };

   		 var form = new FormData();
   		 form.append('name_ingfile', fileInput.files[0]);

   		 xhr.send(form);

		}


}
}
