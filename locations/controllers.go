package main

import (
	"fmt"
	"gopkg.in/mgo.v2"
	"gopkg.in/mgo.v2/bson"
)

type LocationController struct{}

var id int = 0

var url string = "52.53.243.59:27017"


func generateID() int {
	id = id + 1
	return id
}

func (l *LocationController) CreateLocation(location Location) (loc Location, err error) {
	session, err := mgo.Dial(url)
	if err != nil {
		return loc, err
	}
	defer session.Close()

	session.SetMode(mgo.Monotonic, true)

	c := session.DB("cmpe273").C("location")

	location.Id = generateID()
	g := fetchGeocode(location)
	location.Coordinate = g
	err = c.Insert(location)
	if err != nil {
		return loc, err
	}
	return location, nil
}

func (l *LocationController) GetLocation(id int) (loc Location, err error) {
	session, err := mgo.Dial(url)
	if err != nil {
		return loc, err
	}
	defer session.Close()

	session.SetMode(mgo.Monotonic, true)

	c := session.DB("cmpe273").C("location")
	result := Location{}
	err = c.Find(bson.M{"_id": id}).One(&result)
	if err != nil {
		return loc, err
	}
	fmt.Println(result)
	return result, nil
}

func (l *LocationController) DeleteLocation(id int) error {
	session, err := mgo.Dial(url)
	if err != nil {
		return err
	}
	defer session.Close()

	session.SetMode(mgo.Monotonic, true)

	c := session.DB("cmpe273").C("location")
	err = c.Remove(bson.M{"_id": id})
	if err != nil {
		return err
	}
	return nil
}

func (l *LocationController) UpdateLocation(id int, location Location) (loc Location, err error) {
	session, err := mgo.Dial(url)
	if err != nil {
		return loc, err
	}
	defer session.Close()

	session.SetMode(mgo.Monotonic, true)

	c := session.DB("cmpe273").C("location")
	colQuerier := bson.M{"_id": id}
	
	change := bson.M{}
	// Update the address with new coordinates
	if location.Address != "" || location.City != "" || location.Zip != "" {
		original := Location{}
		err = c.Find(bson.M{"_id": id}).One(&original)
		if err != nil {
			return loc, err
		}
		if location.Address == "" {
			location.Address = original.Address 
		}
		if location.City == "" {
			location.City = original.City 
		}
		if location.State == "" {
			location.State = original.State 
		}
		if location.Zip == "" {
			location.Zip = original.Zip 
		}
		location.Coordinate = fetchGeocode(location)
		change = bson.M{"$set": bson.M{"address": location.Address, "city": location.City, "state": location.State, "zip": location.Zip, "coordinates": location.Coordinate}}
	} else if location.Name != "" {
		// Update the location with new name
		change = bson.M{"$set": bson.M{"name": location.Name}}
	}
	
	err = c.Update(colQuerier, change)
	if err != nil {
		return loc, err
	}
	result := Location{}
	err = c.Find(bson.M{"_id": id}).One(&result)
	if err != nil {
		return loc, err
	}
	return result, nil
}
