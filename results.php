<?php
    if(empty($_GET['inputDiameter']) && empty($_GET['diameterUnits']) && empty($_GET['inputDensity']) && empty($_GET['inputVelocity'])){
        echo "Please fill in the fields";
    }else{
        $inputDiameter = $_GET['inputDiameter'];
        $diameterUnits = $_GET['diameterUnits'];
        $inputDensity = $_GET['inputDensity'];
        $inputVelocity = $_GET['inputVelocity'];
        echo ('Welcome:     '. $inputDiameter. '<br/>');
        echo ('This is your email address:'   . $diameterUnits. '<br/>');
        echo ('Welcome:     '. $inputDensity. '<br/>');
        echo ('Welcome:     '. $inputVelocity. '<br/>');
    }
?>