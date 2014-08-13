var table = $(document.querySelector('#resultcount+.resulttable'));
var resultcount = $(document.getElementById('resultcount'));
var passed = table.find('.Passed').length;
var failed = table.find('.Failure').length;
var errors = table.find('.Error').length;
var xfail = table.find('.Expected.Failure').length;
var uxpass = table.find('.Unexpected.Pass').length;
var skipped = table.find('.Skipped').length;

resultcount.find('.Passed')[0].innerHTML += passed;
resultcount.find('.Failure')[0].innerHTML += failed;
resultcount.find('.Error')[0].innerHTML += errors;
resultcount.find('.Expected.Failure')[0].innerHTML += xfail;
resultcount.find('.Unexpected.Pass')[0].innerHTML += uxpass;
resultcount.find('.Skipped')[0].innerHTML += skipped;