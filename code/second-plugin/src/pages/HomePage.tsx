import { Box, Button, Heading, Text, VStack } from "@chakra-ui/react";
import React, { useState, useEffect } from "react";


export const HomePage = () => {
  const [greeting, setGreeting] = useState([]);
  const [loading, setLoading] = useState(true);
  
  console.log("Starting up");

  useEffect(() => {

    fetch("/second-plugin/secondhello")
      .then(response => response.json())
      .then(json => {
	  console.log("Response fetched");
	  console.log(json);
           
          setGreeting(json);
	  setLoading(false);
      })
      .catch(error => console.error('Error fetching data:', error));
      
  }, []);
  

  if (loading) return (<>Loading...</>);

  return (
      <div><h1 class="LHeading">{greeting}</h1></div>
  );
};

