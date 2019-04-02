<html>
    <head>
        <title>Database Records</title>
    </head>
    <body>
        <?php
        $myDatabase = "RUBRIK_LIVEMOUNT_DB";
        $link = mssql_connect("RBK_SQL_HOST\RBK_SQL_INSTANCE", 'SQL_USER', 'SQL_PASSWORD');
        if (!$link || !mssql_select_db($myDatabase, $link)) {
            die('Unable to connect or select database!');
        }
        $query = "SELECT EmailAddressID, EmailAddress, ModifiedDate FROM Person.EmailAddress";
        $result = mssql_query($query);
        $o = '<table id="myTable">
          <thead>
          <tr>
          <th>Email Address ID</th>
          <th>Email Address</th>
          </tr>
          </thead><tbody>';
        while ( $record = mssql_fetch_array($result) )
        {
          $o .= '<tr><td>'.$record ['EmailAddressID'].'</td><td>'.$record ['EmailAddress'].'</td></tr>';
        }
        $o .= '</tbody></table>';
        echo $o;
        mssql_free_result($query);
        ?>
    </body>
</html>