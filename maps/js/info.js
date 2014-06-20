function extractUrlParams(url)
{
    // url = location.search for ex
    var t = url.substring(1).split('&'); //split the second part of the url
var compt=0;
    var f = [];
	
	f[compt]=t[0];
compt++;
    for (var i=1; i<t.length; i++){
        var x = t[ i ].split('='); // take the data from the url
        f[compt]=x[1];
	compt++;
    }


	//console.log(f[0],f[1],f[2],f[3]);
    return f;
}

$(document).ready(function(){
var params = extractUrlParams(location.search);
var endurl=location.search.split('?'); //take the data from the url
var endingurl=endurl[1];
var finalurl="http://127.0.0.1:8000/api/v1/measurement/?point__matchup_id="+endingurl; //url for querying and get data
$.get(
        url=finalurl,
        success=function(data){
		// Write the data into the page
		$("#titleinfo").html('Informations about : ' +params[0]+" "); //title 
		$("#deployment").html('Deployment : ' +data.objects[0].point.deployment.site); // the site
		$("#measuretype").html('Measurement type : ' +data.objects[0].measurementtype.long_name); //the type of the measurement
		//console.log(data.objects[0]);

		if (data.objects[0].wavelength!=null){ // check if the wavelegnths are defined
		$("#wavelength").html('Wavelengths :' +data.objects[0].wavelength.wavelength);} //if they are put them
		else{$("#wavelength").html('Wavelengths : Undefined');}//if not put "Undefined"

		$("#instrument").html('Instrument :' +data.objects[0].instrument.name);//the name of the instrument used to take the data
		$("#type").html('Type : ' +data.objects[0].measurementtype.type);//type of measurement 2nd version
		var times = data.objects[0].point.time_is.split('T'); // take the timefrom the data and formate it
		$("#time").html('These data were taken on :'+times[0]+" at "+times[1]);
		$("#value").html('Value : '+data.objects[0].value+" "+data.objects[0].measurementtype.units);//put the value and its units
		$("#theta").html('Theta : '+data.objects[0].point.thetas_is);// theta
		$("#mqc").html('Mqc : '+data.objects[0].point.mqc);//mqc
		$("#PI").html('PI : '+data.objects[0].point.deployment.pi);// ?
        }, 
        dataType='jsonp' // /!\ NOT SURE IF SAFE         
    );


});
