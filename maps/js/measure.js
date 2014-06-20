$("#submit").click(function() {
	var tableau=[];
	document.getElementById('message').style.visibility="hidden";
    var selectdeploy = document.getElementById("deployment");
	var selecttype = document.getElementById("type");
	var result="";
	var selectwave = document.getElementById("wavelengths");
	surline(document.getElementById('wavelengths'),false);
	surline(document.getElementById('deployment'),false);
	surline(document.getElementById('type'),false);
	if ( selectdeploy.value=="Selection" && selecttype.value=="Selection" && selectwave.value=="Selection"){ // check if the select are still on the Selection option if all them are, returns an error
		document.getElementById('message').innerHTML="Error: Please at least inform the deployment,the type or the wavelengths"; 
		document.getElementById('message').style.color="red";
		document.getElementById('message').style.visibility="visible";
		surline(document.getElementById('wavelengths'),true); //highlight the three fields when they are in error
		surline(document.getElementById('deployment'),true);
		surline(document.getElementById('type'),true);
	}
	// cant be tested now - and to be completed
	/* else if {resultat=="undefined"){
		document.getElementById('message').innerHTML="Error: No such result";
		document.getElementById('message').style.color="red";
		document.getElementById('message').style.visibility="visible";
	} */
	else { 
		var request='http://127.0.0.1:8000/api/v1/measurement/?'
		var endrequest='';
		if (selectdeploy.value!="Selection"){
			endrequest+='point__deployment__site__in='+selectdeploy.value+'&';
		}
		if (selecttype.value!="Selection"){
			endrequest+='measurementtype__long_name__in='+selecttype.value+'&';
		}
		if (selectwave.value!="Selection"){
			endrequest+='wavelength__wavelength__in='+selectwave.value+'.0&';
		}
		endrequest +='/?';
		request+=endrequest;
		console.log(request);
		$.ajaxSetup({async: false});
		$.ajax({ url:request, 
			dataType:'jsonp',
			success:function(data){console.log('test',data);
			
			for(var i=data.objects.length-1; i>-1; i--){
			tableau.push(data.objects[i].point.matchup_id);
			}
			if(tableau.length==0){
document.getElementById('message').innerHTML="No results found";	
document.getElementById('message').style.visibility="visible";
	document.getElementById('deployment').value="Selection";
		document.getElementById('type').value="Selection";

		document.getElementById('wavelengths').value="Selection";

}else{
document.getElementById('message').innerHTML="Result found :";	
var links=[];
for(var d=0;d<tableau.length;d++){
links.push("file:///home/test/mermaid2/maps/info.html?"+tableau[d]+'&'+endrequest);

$('#tableau>tbody:last').append('<tr><td><a href="'+links[d]+'">'+tableau[d]+'</a></td></tr>');
}
//console.log(document.getElementById("tableau").rows[5].cells[0].innerHtml);


document.getElementById('message').style.color="green";
document.getElementById('message').style.visibility="visible";
	document.getElementById('deployment').value="Selection";
		document.getElementById('type').value="Selection";

		document.getElementById('wavelengths').value="Selection";
}},
			error:function(data){			
			console.log("fail",data);},
			
			});
//console.log(result);

		 // + the result, It will be treated later
	
		
	}
	}

);

function surline(field, error){ // highlight the error when there is some
   if(error)
      field.style.backgroundColor = "#fba";
   else
      field.style.backgroundColor = "";
}

$(document).ready(function(){

    $.get(
        url='http://127.0.0.1:8000/api/v1/measurementtype?limit=0&order_by=long_name',
        success=function(data){
		
            for(var i=0; i<data.objects.length; i++){
                $("#type").append($("<option>").val(data.objects[i].long_name).html(data.objects[i].long_name));
            } 
        }, 
        dataType='jsonp' // /!\ NOT SURE IF SAFE         
    );
    
    $.get(
        url='http://127.0.0.1:8000/api/v1/deployment?limit=0&order_by=site',
        success=function(data){

            for(var i=0; i<data.objects.length; i++){
                $("#deployment").append($("<option>").val(data.objects[i].site).html(data.objects[i].site));
            } 
        }, 
        dataType='jsonp' // /!\ NOT SURE IF SAFE         
    );

	$.get(
		url='http://127.0.0.1:8000/api/v1/measurementwavelength/?limit=0&filter_by=wavelength',
		success=function(data){
			for(var i=0; i<data.objects.length; i++){
				$("#wavelengths").append($("<option>").val(data.objects[i].wavelength).html(data.objects[i].wavelength));
			} 
		}, 
		dataType='jsonp' // /!\ NOT SURE IF SAFE         
	);

})
