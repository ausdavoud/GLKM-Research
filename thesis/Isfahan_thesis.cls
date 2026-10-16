
%%
%%  This is file `Tabriz_thesis.cls',
%%  The original file was xepersian-thesis.cls by Vafa Khalighi
%%   __________________________________
%%   Copyright © 2011-2012 Vahid Damanafshan
%%  
%%   http://damanafshan.tk      
%%   http://forum.parsilatex.com
%% 
%% 
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{VThesis}
              [10/21/2011 v0.4
 Persian thesis document class in XeLaTeX for University of Isfahan projects/theses/dissertations]
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}
\ProcessOptions
\LoadClass[a4paper,12pt]{book}
\def\university#1{\gdef\@university{#1}}
\def\department#1{\gdef\@department{#1}}
\def\degree#1{\gdef\@degree{#1}}
\def\thesisdate#1{\gdef\@thesisdate{#1}}
\newcommand{\firstsupervisor}[1]{\def\@firstsupervisor{#1}}
\newcommand{\secondsupervisor}[1]{\def\@secondsupervisor{#1}}
\newcommand{\firstadvisor}[1]{\def\@firstadvisor{#1}}
\newcommand{\secondadvisor}[1]{\def\@secondadvisor{#1}}
\def\name#1{\gdef\@name{#1}}
\def\surname#1{\gdef\@surname{#1}}
\def\keywords#1{\gdef\@keywords{#1}}
\def\fa-abstract#1{\gdef\@fa-abstract{#1}}
\def\faculty#1{\gdef\@faculty{#1}}
\def\subject#1{\gdef\@subject{#1}}
\def\field#1{\gdef\@field{#1}}
\def\department#1{\gdef\@department{#1}}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\def\latintitle#1{\gdef\@latintitle{#1}}
\def\latinauthor#1{\gdef\@latinauthor{#1}}
\def\latindegree#1{\gdef\@latindegree{#1}}
\def\latinfaculty#1{\gdef\@latinfaculty{#1}}
\def\latinthesisdate#1{\gdef\@latinthesisdate{#1}}
\def\latinsubject#1{\gdef\@latinsubject{#1}}
\def\latinfield#1{\gdef\@latinfield{#1}}
\def\firstlatinsupervisor#1{\gdef\@firstlatinsupervisor{#1}}
\def\secondlatinsupervisor#1{\gdef\@secondlatinsupervisor{#1}}
\def\firstlatinadvisor#1{\gdef\@firstlatinadvisor{#1}}
\def\secondlatinadvisor#1{\gdef\@secondlatinadvisor{#1}}
\def\latinname#1{\gdef\@latinname{#1}}
\def\latinsurname#1{\gdef\@latinsurname{#1}}
\def\en-abstract#1{\gdef\@en-abstract{#1}}
\def\latinkeywords#1{\gdef\@latinkeywords{#1}}
\def\latinuniversity#1{\gdef\@latinuniversity{#1}}
%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newif\if@bscthesis
\@bscthesisfalse
\DeclareOption{bsc}{\@bscthesistrue}
\newif\if@mscthesis
\@mscthesisfalse
\DeclareOption{msc}{\@mscthesistrue}
\ProcessOptions
%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand{\vtitle}{\begin{titlepage}
%\topmargin=-30pt
\vspace{-2cm}\centerline{{\includegraphics[height=3.5cm]{logo}}}
\vspace{-.8cm}
{\large\@university\par

\vspace{-.8cm}\large\@faculty\par

\vspace{-1cm}\@department}
\vskip .5cm
 \if@mscthesis
{\large\bfseries پایان‌نامه}
\else
 \if@bscthesis
 {\large\bfseries پروژه }
 \else
{\large\bfseries رساله
\fi\fi
\if@mscthesis
کارشناسی ارشد
\else
\if@bscthesis
کارشناسی
\else
دکتری
\fi\fi
}
{\large\bfseries{ رشته}}
{\large \bfseries\@subject% 
\hskip .05cm \if@mscthesis%
 گرایش
\else
\if@bscthesis%
\relax%
\else%
 گرایش
\fi\fi
\@field}
\vskip 1cm
%\baselineskip=.750cm

\vskip -.5cm
 {\huge\bfseries {\baselineskip=1cm \@title}}\baselineskip=1.5cm\par
\vskip .8cm
 \baselineskip=.5cm
\large
{\ifx\@firstsupervisor\undefined%
\ifx\@secondsupervisor\undefined%
\else\fi
\else
\ifx\@secondsupervisor\undefined%
استاد راهنما:
{\Large\bfseries\par
\@firstsupervisor}
\else
\large
استادان راهنما:
\par
{\Large\bfseries \@firstsupervisor{}
\vskip .05cm
 \@secondsupervisor}
\fi\fi}
\par\large
{\ifx\@firstadvisor\undefined%
\ifx\@secondadvisor\undefined%
\else\fi
\else
\ifx\@secondadvisor\undefined%
استاد مشاور:
{\Large\bfseries\par
\@firstadvisor}
\else

\large
استادان مشاور:
\par
{\Large\bfseries\@firstadvisor{} و \@secondadvisor}
\fi\fi}

\vskip 1cm

{\large%
  \by}\par
{\Large\bfseries{\large\bfseries   \@name\@surname}}\par
\vskip 6mm
%\vfill
{\large \@thesisdate}
%\vfill
\end{titlepage}%
\newpage
\thispagestyle{empty}
\baselineskip=.7cm
\if@bscthesis \relax
\else

\fi
}
\def\frame{\newpage
\thispagestyle{empty}
\begin{framed}\thispagestyle{empty}}
\def\endframe{\thispagestyle{empty}\end{framed}
\thispagestyle{empty}
\newpage
}
\def\abstractpage{\newpage
\thispagestyle{empty}
\vskip 15mm
\par
\begin{abstract}}
\def\endabstractpage{\end{abstract}
\newpage
}

\def\latinabstract{\newpage
\thispagestyle{empty}
\vskip 15mm
\begin{center}{\Large\bfseries \@latintitle \\[5mm]}
{\bfseries Abstract}
\end{center}
\vspace{5mm}}

\def\endlatinabstract{\newpage}

\def\acknowledgementpage{\newpage
\thispagestyle{empty}

\vspace{1cm}
\par\noindent}
\def\endacknowledgementpage{\newpage}

\def\titlepage{\newpage\centering
  \thispagestyle{empty}
  \parindent 0pt \parskip 10pt plus 1fil minus 1fil
  \def\baselinestretch{1}\@normalsize\vbox to \vsize\bgroup\vbox to 9in\bgroup}
\def\endtitlepage{\par\kern 0pt\egroup\vss\egroup\newpage}

\def\signature{\vspace{1cm}
\begin{flushleft}
{\nastaliq \scriptsize \@name\ \@surname \\
\@thesisdate}
\end{flushleft}}

\def\abstract{\subsection*{\abstractname}\small
\@normalsize}
\def\endabstract{\par}

%\pagenumbering{harfi}
%\let\ol@chapter\@chapter
%\def\@chapter{%
%  \ifnum\c@chapter=0 \pagenumbering{arabic}\setcounter{page}{1}\fi
%  \ol@chapter}

\font\titlefont=cmssbx10 scaled 2074
\font\supervisorfont=cmbxti10

\newcommand{\latinvtitle}{%
\if@bscthesis \relax
\else
\begin{titlepage}
\vspace{-2cm}{\includegraphics[height=3.5cm]{logo}}
\centerline{\bf \@latinuniversity} 
\large\bfseries
\@latinfaculty\space 
\vskip 5mm
%{
 \if@mscthesis
Dissertation Submitted in Partial 
\\[.2cm]
 Fulfillment of The Requirements For The
\\[.2cm]
Degree of Master of Science in\par
\else
Doctoral Thesis Submitted in Partial 
\\[.2cm]
Fulfillment of The  Requirements For The
\\[.2cm]
Degree of Doctor of Science in \par
\fi
{\large\bfseries \@latinsubject}
\vskip 1.5cm
\baselineskip=.750cm
{\titlefont \@latintitle}
\baselineskip=.750cm \par
%\addtolength{\baselineskip}{-5mm}
\vskip 1.5cm
\large
{\ifx\@firstlatinsupervisor\undefined%
\ifx\@secondlatinsupervisor\undefined%
\else\fi
\else
\ifx\@secondlatinsupervisor\undefined%
Supervisor
{\Large\bfseries\par
\@firstlatinsupervisor}
\else
\large
Supervisors
\par
{\Large\bfseries \@firstlatinsupervisor{} and \@secondlatinsupervisor}
\fi\fi}
\vskip .75cm
\par
\large
{\ifx\@firstlatinadvisor\undefined%
\ifx\@secondlatinadvisor\undefined%
\else\fi
\else
\ifx\@secondlatinadvisor\undefined%
Advisor
{\Large\bfseries\par
\@firstlatinadvisor}
\else

\large
Advisors
\par
{\Large\bfseries\@firstlatinadvisor{} and \@secondlatinadvisor}
\fi\fi}
\vskip 1.5cm
{\bfseries\latinby}\par
{\large %\supervisorfont
\rm\@latinname \; \@latinsurname}\par
\vskip 5mm

\par
\vskip 2cm

{\@latinthesisdate}
\par
\vskip 1cm

\par

\vfill
%
\end{titlepage}
\fi}

\def\onvan{عنوان}
\def\writtenfor{برای دریافت درجه }
\def\by{پژوهشگر:}
\def\latinby{by}
\def\cleardoublepage{\clearpage\if@twoside \ifodd\c@page\else
\hbox{}
\thispagestyle{empty}
\newpage
\if@twocolumn\hbox{}\newpage\fi\fi\fi}


