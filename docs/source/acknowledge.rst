.. include:: ./substitutions.rst

Acknowledging ampycloud
=======================

1. Only use lower case letters when mentioning ampycloud, and always include the version number.
   Ideally, you should also include the Digital Object Identifier (DOI) associated to the specific
   release you have been using:

   ampycloud |version| |doi|

2. If ampycloud was useful for your research, please cite the dedicated article:

   .. todo::

      When the time comes, include here the link to the dedicated ampycloud article.

3. ampycloud relies on external Python libraries that require & deserve to be acknowledged in their
   own right. The following LaTeX blurb is one way to do so:

   .. code-block:: latex

        This research has made use of \textit{ampycloud vX.Y.Z} \citep[DOI:][]{TBD}
        Python package. \textit{ampycloud} relies, in part, on the following Python packages:
        \textsc{matplotlib} \citep{Hunter2007}, \textit{numpy} \citep{Oliphant2006, Van2011},
        \textsc{pandas} \citep{McKinney2010,reback2020},
        \textit{scikit-learn} \citep{Pedregosa2011}, \textsf{scipy} \citep{Virtanen2020},
        and \textit{statsmodels} \citep{seabold2010}.

        @article{Hunter2007,
          Author    = {Hunter, J. D.},
          Title     = {Matplotlib: A 2D graphics environment},
          Journal   = {Computing in Science \& Engineering},
          Volume    = {9},
          Number    = {3},
          Pages     = {90--95},
          abstract  = {Matplotlib is a 2D graphics package used for Python for
          application development, interactive scripting, and publication-quality
          image generation across user interfaces and operating systems.},
          publisher = {IEEE COMPUTER SOC},
          doi       = {10.1109/MCSE.2007.55},
          year      = 2007
        }

        @InProceedings{ McKinney2010,
          author    = { {W}es {M}c{K}inney },
          title     = { {D}ata {S}tructures for {S}tatistical {C}omputing in {P}ython },
          booktitle = { {P}roceedings of the 9th {P}ython in {S}cience {C}onference },
          pages     = { 56 - 61 },
          year      = { 2010 },
          editor    = { {S}t\'efan van der {W}alt and {J}arrod {M}illman },
          doi       = { 10.25080/Majora-92bf1922-00a }
        }

        @book{Oliphant2006,
          title     = {A guide to NumPy},
          author    = {Oliphant, Travis E},
          volume    = {1},
          year      = {2006},
          publisher = {Trelgol Publishing USA}
        }

        @article{Pedregosa2011,
         title={Scikit-learn: Machine Learning in {P}ython},
         author={Pedregosa, F. and Varoquaux, G. and Gramfort, A. and Michel, V.
                 and Thirion, B. and Grisel, O. and Blondel, M. and Prettenhofer, P.
                 and Weiss, R. and Dubourg, V. and Vanderplas, J. and Passos, A. and
                 Cournapeau, D. and Brucher, M. and Perrot, M. and Duchesnay, E.},
         journal={Journal of Machine Learning Research},
         volume={12},
         pages={2825--2830},
         year={2011}
        }

        @software{reback2020,
            author  = {The pandas development team},
            title   = {pandas-dev/pandas: Pandas},
            month   = feb,
            year    = 2020,
            publisher = {Zenodo},
            version = {latest},
            doi     = {10.5281/zenodo.3509134},
            url     = {https://doi.org/10.5281/zenodo.3509134}
        }

        @inproceedings{seabold2010,
            title={statsmodels: Econometric and statistical modeling with python},
            author={Seabold, Skipper and Perktold, Josef},
            booktitle={9th Python in Science Conference},
            year={2010},
        }

        @article{Van2011,
          title     = {The NumPy array: a structure for efficient numerical computation},
          author    = {Van Der Walt, Stefan and Colbert, S Chris and Varoquaux, Gael},
          journal   = {Computing in Science \& Engineering},
          volume    = {13},
          number    = {2},
          pages     = {22},
          year      = {2011},
          publisher = {IEEE Computer Society}
        }

        @ARTICLE{Virtanen2020,
            author  = {Virtanen, Pauli and Gommers, Ralf and Oliphant, Travis E. and
            Haberland, Matt and Reddy, Tyler and Cournapeau, David and
            Burovski, Evgeni and Peterson, Pearu and Weckesser, Warren and
            Bright, Jonathan and {van der Walt}, St{\'e}fan J. and
            Brett, Matthew and Wilson, Joshua and Millman, K. Jarrod and
            Mayorov, Nikolay and Nelson, Andrew R. J. and Jones, Eric and
            Kern, Robert and Larson, Eric and Carey, C J and
            Polat, {\.I}lhan and Feng, Yu and Moore, Eric W. and
            {VanderPlas}, Jake and Laxalde, Denis and Perktold, Josef and
            Cimrman, Robert and Henriksen, Ian and Quintero, E. A. and
            Harris, Charles R. and Archibald, Anne M. and
            Ribeiro, Ant{\^o}nio H. and Pedregosa, Fabian and
            {van Mulbregt}, Paul and {SciPy 1.0 Contributors}},
            title   = {{{SciPy} 1.0: Fundamental Algorithms for Scientific
            Computing in Python}},
            journal = {Nature Methods},
            year    = {2020},
            volume  = {17},
            pages   = {261--272},
            adsurl  = {https://rdcu.be/b08Wh},
            doi     = {10.1038/s41592-019-0686-2},
            }