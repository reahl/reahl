 Reahl is a web application framework that allows a Python programmer to work in 
 terms of useful abstractions - using a single programming language.

 Stubble (a part of the Reahl development tools) is a collection of
 tools for writing stubs in unit tests. Stubble can be used independently
 of the Reahl web framework.

 Using stubs allows one to decouple one unit test from real code 
 unrelated to it - you write a fake class to take the place of 
 a real one (which this test is not testing).

 Stubble ensures, however, that the test will break should the
 interface of the stub differ from that of the real class it is a stub
 for.
