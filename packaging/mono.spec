%{!?dotnet_buildtype: %define dotnet_buildtype Release}

%define dotnet_version  3.0.0

Name:		mono
Version:	6.0.0
Release:	0
Summary:	Microsoft .NET Runtime, Coreclr
Group:		Development/Languages
License:	MIT
URL:		http://github.com/dotnet/coreclr
Source0: %{name}-%{version}.tar.gz
Source1: %{name}.manifest
Source2: coreclr_env.list

%ifarch %{arm}
BuildRequires:  patchelf
%endif

%ifarch %{ix86}
BuildRequires:  patchelf
BuildRequires:  glibc-64bit
BuildRequires:  libgcc-64bit
BuildRequires:  libstdc++-64bit
BuildRequires:  libunwind-64bit
BuildRequires:  libuuid-64bit
BuildRequires:  zlib-64bit
BuildRequires:  libopenssl-64bit
%endif

BuildRequires:  python
BuildRequires:  cmake
BuildRequires:  coreclr

# Accelerate python
%ifarch %{arm}
BuildRequires: python-accel-armv7l-cross-arm
%endif

%ifarch aarch64
BuildRequires: python-accel-aarch64-cross-aarch64
%endif

%description
Mono open source ECMA CLI, Csharp and .NET implementation.

%package devel
Summary:    Mono Development package
Requires:   mono

%description devel
Headers and static libraries

# .NET Core Runtime
%define netcoreappdir   %{_datadir}/dotnet/shared/Microsoft.NETCore.App/%{dotnet_version}

# .NET Tizen Runtime
%define dotnettizendir  %{_datadir}/dotnet.tizen
%define dotnetlibdir    %{dotnettizendir}/lib

%prep
%setup -q -n %{name}-%{version}
cp %{SOURCE1} .
cp %{SOURCE2} .

%ifarch %{arm} %{ix86}
%ifarch %{arm}
# Detect interpreter name from cross-gcc
LD_INTERPRETER=$(patchelf --print-interpreter /emul/usr/bin/gcc)
LD_RPATH=$(patchelf --print-rpath /emul/usr/bin/gcc)
for file in $( find ./.dotnet -name "dotnet" -type f)
do
    patchelf --set-interpreter ${LD_INTERPRETER} ${file}
    patchelf --set-rpath ${LD_RPATH}:%{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
for file in $( find ./.dotnet ./libicu-57.1 -iname "*.so" -or -iname "*.so.*" )
do
    patchelf --set-rpath ${LD_RPATH}:%{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
%endif
%ifarch %{ix86}
for file in $( find ./.dotnet ./libicu-57.1 -iname "*.so" -or -iname "*.so.*" )
do
    patchelf --set-rpath %{_builddir}/%{name}-%{version}/libicu-57.1/ ${file}
done
%endif
%endif

%build
# disable asan build when global forced asan build
%{?asan:export ASAN_OPTIONS=use_sigaltstack=false:`cat /ASAN_OPTIONS`}
%{?asan:/usr/bin/gcc-unforce-options}
%{?asan:export LD_LIBRARY_PATH=`pwd`/libicu-57.1}

./autogen.sh --with-core=only --prefix=%{netcoreappdir}
touch netcore/.configured

export NUGET_PACKAGES=`pwd`/.packages

cd netcore
./build.sh --configuration %{dotnet_buildtype} /p:DotNetBuildOffline=true

%install

mkdir -p %{buildroot}%{netcoreappdir}
mkdir -p %{buildroot}%{dotnetlibdir}

%make_install

ln -sf %{netcoreappdir} %{buildroot}/%{dotnettizendir}/netcoreapp
ln -sf %{netcoreappdir}/lib/libmono-2.0.so %{buildroot}%{netcoreappdir}/libcoreclr.so
cp netcore/System.Private.CoreLib/bin/arm/System.Private.CoreLib.dll %{buildroot}%{netcoreappdir}
cp %{netcoreappdir}/System.Globalization.Native.so %{buildroot}%{netcoreappdir}
cp coreclr_env.list %{buildroot}%{dotnetlibdir}

%files
%manifest %{name}.manifest
%{netcoreappdir}/bin/*
%{netcoreappdir}/lib/*
%{netcoreappdir}/libcoreclr.so
%{netcoreappdir}/System.Private.CoreLib.dll
%{netcoreappdir}/System.Globalization.Native.so
%{dotnettizendir}/netcoreapp
%{dotnetlibdir}/coreclr_env.list

%files devel
%manifest %{name}.manifest
%{netcoreappdir}/include/*
%{netcoreappdir}/share/*