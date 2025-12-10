This page provides details of the major features of object oriented programming and definitions of terminology.

## Objects

-   An *object* often models a real-world thing - person, animal, shape, car
-   Collection of *attributes* and *behaviors*
-   Defined as a *class* with *member variables* and *methods*
-   An *instance* of a class is an occurance of an object that has been created using the class *constructor*
-   A class *constructor* method is called automatically when a new instance of a class is created.
-   A *destructor* method is called automatically when an instance of a class is destroyed.

## Encapsulation

-   Bundle data (attributes) with the methods that operate on the data
-   Restrict access to the data using *access modifiers* like *private* (only accessable within self) and *protected* (available to subclasses as well)
-   Best Practices
    -   Keep member variables private
    -   Provide accessor functions to attributes when needed
    -   Public methods provide an interface to the rest of the world, everthing else should be private
-   Benefit: reduce complexity, increases robustness, by limiting the interdependencies between components.

## Inheritance

-   Reuse code by basing an object on another object
-   Terminology
    -   Superclass, base class, parent class
    -   Subclass, derived class, child class
-   Examples
    -   parent: Animal, children: Person, Cat, Fish
    -   parent: MotorVehicle, children: Car, Truck, Bus, Tractor
    -   parent: Shape, children: Ellipse, Rectangle, Triangle, Cone
-   *Child classes* inherit attributes and behaviors from *parent classes*
-   Child classes may *override* behaviors inherited from parent classes by providing it's own implementation of a method.
-   An *abstract method* in a parent class does not have an implementation. Child classes MUST provide an implementation to be instantiated.
-   An *abstract class* has at least one abstract method and cannot be instantiated.
-   A *virtual method* in a parent class provides a default implementation that MAY be overriden by the child classes.

## Polymorphism

-   Objects of different types (or classes) can be defined with the same interface and respond to method calls with the appropriate type-specific behavior.
-   The exact type of the object is determined at run-time, so the program does not need to determine type in advance.
-   Examples
    -   Draw every shape in a collection of shapes. The collection has Rectangles and Triangles, both based on the Shape class, which has an abstract method called Draw().
    -   Make a collection of different animals talk. Code example shown below.

## PHP example

    interface IAnimal {
        function getName();
        function talk();
    }

    abstract class AnimalBase implements IAnimal {
        protected $name;

        public function __construct($name) {
            $this->name = $name;
        }

        public function getName() {
            return $this->name;
        }
    }

    class Cat extends AnimalBase {
        public function talk() {
            return 'Meowww!';
        }
    }

    class Dog extends AnimalBase {
        public function talk() {
            return 'Woof! Woof!';
        }
    }

    $animals = array(
        new Cat('Missy'),
        new Cat('Mr. Mistoffelees'),
        new Dog('Lassie')
    );

    foreach ($animals as $animal) {
        echo $animal->getName() . ': ' . $animal->talk();
    }

## Python Example

    class Animal:
        def __init__(self, name):    # Constructor of the class
            self.name = name
        def talk(self):              # Abstract method, defined by convention only
            raise NotImplementedError("Subclass must implement abstract method")

    class Cat(Animal):
        def talk(self):
            return 'Meow!'

    class Dog(Animal):
        def talk(self):
            return 'Woof! Woof!'

    animals = [Cat('Missy'),
               Cat('Mr. Mistoffelees'),
               Dog('Lassie')]

    for animal in animals:
        print animal.name + ': ' + animal.talk()

    # prints the following:
    #
    # Missy: Meow!
    # Mr. Mistoffelees: Meow!
    # Lassie: Woof! Woof!
