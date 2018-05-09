# Fellyjish
### CS244 Assignment 2 (Spring 2018) - Jellyfish Reproduction

Diveesh Singh and Jean-Luc Watson

Reproduces Figure 9 and Table 1 from the Jellyfish NSDI paper located [here](https://people.inf.ethz.ch/asingla/papers/jellyfish-nsdi12.pdf).

#### [Final Report](https://docs.google.com/document/d/1Cr5j943CcmmKixRylXLq7XA-QLYyADSkCS0xwgt2-RE/edit?usp=sharing)

#### Instructions

  1. Start a Google Compute instance. We used these default specs:

  ```
  1 vCPU with 3.75 GB memory
  Debian GNU/Linux 9 (stretch)
  us-west1-a
  ```

  2. Install git (`sudo apt install git`) and clone this repository:

  ```
  $ git clone https://github.com/jlwatson/fellyjish
  ```

  3. Set up the project:

  ```
  $ cd fellyjish
  $ ./setup_project.sh
  ```

  You will need to type `Y` to confirm various package installations. The script will install Mininet 2.2.2 from source, as well as `networkx` and `matplotlib`.

  4. Generate the recreated results:

  ```
  $ sudo python main.py
  ```

  The table should appear in your console output, while our recreation of Figure 9 can be found by default in the top level repository folder as the file `figure9.eps`. Open and enjoy!


